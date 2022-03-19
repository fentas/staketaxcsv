# known contracts from protocol
CONTRACTS = [
    # SPEC Platform
    "terra1vvu80qnl0yn94stkc9sy2f5xcqcscu2fercgzq",
    # SPEC Token
    "terra1s5eczhe0h0jutf46re52x5z4r03c8hupacxmdr",
    # SPEC Governance
    "terra1dpe4fmcz2jqk6t50plw0gqa2q3he2tj6wex5cl",
    # SPEC Staking
    "terra1fxwelge6mf5l6z0rjpylzcfq9w9tw2q7tewaf5",
    # SPEC Farm
    "terra17hjvrkcwn3jk2qf69s5ldxx5rjccchu35assga",
    # SPEC Mirror Farm
    "terra1kehar0l76kzuvrrcwj5um72u3pjq2uvp62aruf",
    # SPEC Anchor Farm
    "terra1fqzczuddqsdml37a20pysjx5wk9dh4tdzu2mrw",
    # SPEC Valkyrie Farm
    "terra1xt4ugaxds6wjehjckqchzg4e99n3cjd2rtfw4f",
    # SPEC Nexus Psi-UST Farm
    "terra1j2hdp4jelqe9tkfwnsx5mlheqagaryxhqwr4h2",
    # SPEC Orion Farm
    "terra106en784zr4kpe6phlaj8c8t3aeqgn3xsugaelx",
    # SPEC Terraworld Farm
    "terra1cdyw7fydevn372re7xjgfh8kqrrf2lxm5k6ve3",
    # SPEC Nexus nEth-Psi Farm,
    "terra1lmm7xjareer3fd040kz2epw93hg20p9f64uh98",
    # SPEC Nexus nLuna-Psi Farm,
    "terra19kzel57gvx42e628k6frh624x5vm2kpck9cr9c",
    # SPEC bPsiDP-24m Farm
    "terra1kr82wxlvg773vjay95epyckna9g4vppjyfxgd0",
    # Spectrum SPEC-UST Pair
    "terra1tn8ejzw8kpuc87nu42f6qeyen4c7qy35tl8t20",
]

def handle(exporter, elem, txinfo, contract):
    print('SPEC!')
    #print(elem)
