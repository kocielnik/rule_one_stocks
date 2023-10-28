from rule_one import Company, Deal, MockTicker


def test_get_deals():
    companies = [
        Company(symbol="tsm", sticker_price=11),
        Company(symbol="msft", sticker_price=118)
    ]

    deals = Deal.from_(companies, Ticker=MockTicker)

    assert deals[0] == Deal(
        symbol='msft', sticker_price=118, price=352.5, percent_of_sticker=299
    )
