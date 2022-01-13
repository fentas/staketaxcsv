
import os
import boto3
import logging

# until merged https://github.com/boto/boto3/pull/2746
AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")

STAGE = os.environ.get("STAGE")
DYNAMO_TABLE_CACHE = "prod_cache" if STAGE == "prod" else "dev_cache"
FIELD_SOL_BLOCKS = "sol_blocks"
FIELD_TERRA_CURRENCY_ADDRESSES = "terra_currency_addresses"
FIELD_OSMO_IBC_ADDRESSES = "osmo_ibc_addresses"

class Cache:

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', endpoint_url=AWS_ENDPOINT_URL)
        self.table = self.__ensure_table()

    def __ensure_table(self):
        table_names = [table.name for table in self.dynamodb.tables.all()]
        if DYNAMO_TABLE_CACHE not in table_names:
            self.dynamodb.create_table(
                AttributeDefinitions=[
                    {
                        'AttributeName': 'field',
                        'AttributeType': 'S',
                    },
                ],
                KeySchema=[
                    {
                        'AttributeName': 'field',
                        'KeyType': 'HASH',
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1,
                },
                TableName=DYNAMO_TABLE_CACHE,
            )
        
        return self.dynamodb.Table(DYNAMO_TABLE_CACHE)

    def _set_overwrite(self, field_name, data):
        response = self.table.put_item(
            Item={
                'field': field_name,
                'data': data
            }
        )
        logging.info("Updated %s ", field_name, extra={"response": response})

    def _set_merge(self, field_name, data):
        prev_data = self._get(field_name)
        prev_data.update(data)

        self._set_overwrite(field_name, prev_data)

    def _get(self, field_name):
        response = self.table.get_item(
            Key={'field': field_name}
        )

        if "Item" not in response:
            logging.warning("_get(): Unable to retrieve for field_name=%s", field_name)

            return {}
        item = response['Item']
        logging.info("Retrieved %s data.", field_name)
        data = item['data']
        return data

    def set_sol_blocks(self, data):
        self._set_merge(FIELD_SOL_BLOCKS, data)

    def get_sol_blocks(self):
        return self._get(FIELD_SOL_BLOCKS)

    def set_terra_currency_addresses(self, data):
        return self._set_merge(FIELD_TERRA_CURRENCY_ADDRESSES, data)

    def get_terra_currency_addresses(self):
        return self._get(FIELD_TERRA_CURRENCY_ADDRESSES)

    def set_osmo_ibc_addresses(self, data):
        return self._set_merge(FIELD_OSMO_IBC_ADDRESSES, data)

    def get_osmo_ibc_addresses(self):
        return self._get(FIELD_OSMO_IBC_ADDRESSES)
