0. Swap our ETH for WETH 
1. Deposit some ETH Into aave
2. Borrow some asset with the ETH collateral 
    1. Sell that borrowed asset (Short selling)
3. Repay everything back 


Testing: 
- Integration test: Kovan
- Unit test: mainnet-fork! (we will mock the entire network)
- NO calen mocks perque no estem cridant cap api o cap chainlink, cap oracle