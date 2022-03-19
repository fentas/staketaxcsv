# known contracts from protocol
CONTRACTS = [
    # Token | GPLOOT
    # https://lunaloot.com/galactic-loot/
    "terra19wnw6rvsv5mmgnphykndk4udrc9nmajj4qrukj",
    # whitelist - Cosmic Colonist Cat | Terra NFT Project
    "terra1pd23ngdmnp2x8a3sraxpeph5ytf6n4tus38lel",
    # ? - some scoring
    "terra1p6jy3efvec0hddkcf86gpjsrnvuum6dsr5yxr0",
    # ? - provide_liquidity
    "terra1xlstmfa83h68xe0sdzur9hlreszp24dd7azm2c",
    # "Congratulations on $100 LUNA" - NFT drop
    "terra1snja2twmwx656qp6juq8jpah4h80pxvwsgsvev",
    # ? - admin_set_tree ~ player
    "terra1yv0x3snxr3uat2kwyd7t0anlpgvw5fcraen9kr",
    "terra1nlsfl8djet3z70xu2cj7s9dn7kzyzzfz5z2sd9",
    # NFT Drop - "The Galactic Punks Comic: Volume 1"
    "terra15fsmmhn5xyfggeeumfxac2ypljna3cstcgfvs6",
]


from common.ExporterTypes import TX_TYPE_UNKNOWN


def handle(exporter, elem, txinfo, contract):
    print(f"UNSPECIFIC! {contract}")
    #print(elem)

    return TX_TYPE_UNKNOWN
