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
    # Some other nft airdrop
    "terra1h6ak3m5h9vw5su7eqfx378vuapd9hsl63slhkl",
    # hm? a:{ b: [...addresses] }
    "terra19scq0wz8grg3sslysmz670mhqqt8lm5t8z4ex0",
    # hm? {batch_add_addresses: allocations: [...{address, allocation}]}
    "terra1a004ax5jrfc8u896rmwm2qgd3vunl3c37n36jw",
    # yet lot nft collections
    "terra177stlhye6zy9ykxtmkng9s2ngevr66vghvyz7x",
    "terra1ffndk5kry8c7r7mudasldzkz28wjavlh8khawj",
    # more nft ... - protocol: "Terranauts",
    "terra13q7gj95yldpnmz4hgec78t5h7vtgn7ueapez5h",
    # register airdrop from luart or stt?
    "terra1ntuz8g4g5pthr52a9ll5ac6ty8gskn2mwx2q4q",
    "terra16hkp0fhqpddkknef9gdpqm369ne07ujy48fyjj", #<second
    #todo's ... 
    "terra1lfr4aja5a2xpxvnrl4gyjpru0wwglu7k87jmeq", # hero swapp 2 > 1 villan
    "terra13ukec8vdz9vra3tdla6dnw477ldgnzcn7wdw9q", # villan mit
]


from common.ExporterTypes import TX_TYPE_UNKNOWN


def handle(exporter, elem, txinfo, contract):
    #print(f"UNSPECIFIC! {contract}")
    #print(elem)

    return TX_TYPE_UNKNOWN
