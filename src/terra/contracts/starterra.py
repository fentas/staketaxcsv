# known contracts from protocol
CONTRACTS = [
    # STT Governance,
    "terra1megftnaw3v9jh9fg2wzejx6d2swncg7ug97tvt",
    # STT Staking Faction Degens
    "terra1z9et2n9ltdqle2s7qq0du2zwr32s3s8ulczh0h",
    # STT/LP Staking Faction Degens
    "terra1pafra8qj9efnxhv5jq7n4qy0mq5pge8w4k8s2k",
    # STT KYC Vault
    "terra1ru8qeh0mvf8m80vul84wsljqvltm6t64n8gjr0",
    # STT Signing
    "terra1mz8qcfplg3s46zkkj9jywmguehpenhahcqc22q",
    # STT IDO Prefund
    "terra1yzewp648fwq7ymlfdg5h90dfzk5y2hf6kk9pdm",
    "terra189q70vz960kg745zacmlp6y2ncjnqxw8h305zq",
    # STT Join IDO
    "terra1uxa6w7f2m4swp7j70auxcjuj8yk9d3ahwqltdl",
    "terra13tfgwcwf8ksx97fcrdwk4v9tk7h5uukw05nrle",
    "terra18d59cack0nhl8epzdym6rr0xlllgxfnn4atdyf",
    "terra1egt808pjkrlftc28m6e5jxxh2u2hmrrt83ax36",
    "terra1plwvxr0923thz8hzcccstvtj2qj8zxfzzren7m",
    "terra1mt586exx4sce39jpll8vm2qmrls5ypmryqhwuf",
    "terra1dxu83nyphufjk9268d87g6gjsl264tu3lrz2a2",
    "terra1wufxrwmhyf3cq7dmmwxkq59zxku4ujeyhle973",
    # STT Vesting Account
    "terra1hzjt8zwty2acna2c3dz8ldhmeyh5tx7glv8t0l",
    # STT Orion Vesting
    "terra140tsjtwlvemglcxrd6kkt39x9c7lfuk5rkjk9m",
    # STT PlayNity Vesting
    "terra1gndu6x3j57znc3yec9t5kayahdr0a6dx4xtj29",
    # Loop IDO Round 1
    "terra1k9zwyjvhquklayg607ahex7egef7a3ujlhny99",
    # STT Kujira Vesting
    "terra1rhckhztwftc7a9u8gyasug0qwwwhzsxsnglm2e",
    # Kujira Airdrop
    "terra1ecrwqx4dy67p8l0vqgz9le6vgktx9lc0djuvwd",
    # Register address
    "terra1tjkra2g2n2twjkr7l4w6tjgaeh0uymesun8cmv",
]

def handle(exporter, elem, txinfo, contract):
    print(f"StarTerra! {contract}")
    #print(elem)
