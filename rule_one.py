"""
Sue is a Rule One Investor.

She wants to check stock prices daily to see if any Rule One deals are available
for her.

For simplicity and robustness of examples, the `Ticker` class in these examples
is replaced with MockTicker.

When Sue uses this program, she always omits the part `Ticker=MockTicker`.


One day, Sue wants to check the price of a single stock.

>>> company = Company(symbol="tsm", sticker_price=11)
>>> get_deal(company, Ticker=MockTicker)
Deal(symbol='tsm', sticker_price=11, price=98, percent_of_sticker=891)


On another day, Sue has several companies she wants to check the price of.

To the same method `get_deal`, she can pass a list of companies the same way
she passed a single company.

>>> companies = [
...  Company(symbol="msft", sticker_price=118),
...  Company(symbol="tsm", sticker_price=11)
... ]
>>> deals = get_deal(companies, Ticker=MockTicker)
>>> deals[0]
Deal(symbol='msft', sticker_price=118, price=352.5, percent_of_sticker=299)
>>> deals[1]
Deal(symbol='tsm', sticker_price=11, price=98, percent_of_sticker=891)


Sue wants the results to be sorted in the order of the best deal available.

Best deal means the largest Margin of Safety (MOS).

If companies are not sorted in the order of the best deal, the results *should*
be.

Note the order of input companies is reversed with respect to the previous example.

>>> companies = [
...  Company(symbol="tsm", sticker_price=11),
...  Company(symbol="msft", sticker_price=118)
... ]
>>> deals = get_deal(companies, Ticker=MockTicker)
>>> deals[0]
Deal(symbol='msft', sticker_price=118, price=352.5, percent_of_sticker=299)


Sue says the interface is too complicated for her, and she would love to
be able to initialize Deal instances directly from Company instances.

>>> companies = [
...  Company(symbol="tsm", sticker_price=11),
...  Company(symbol="msft", sticker_price=118)
... ]
>>> deals = Deal.from_(companies, Ticker=MockTicker)
>>> deals[0]
Deal(symbol='msft', sticker_price=118, price=352.5, percent_of_sticker=299)
"""

from typing import NamedTuple
from yfinance import Ticker
from requests import get
from functools import lru_cache


class Company(NamedTuple):
    symbol: str
    sticker_price: float


class Deal(NamedTuple):

    symbol: str
    sticker_price: float
    price: float
    percent_of_sticker: int

    """
    Sue wants to print an instance of this class and be able to copy-paste
    it into another place, or save it for later pasting.

    >>> Deal(symbol='msft', sticker_price=1, price=1)
    Deal(symbol='msft', sticker_price=1, price=1)


    Sue wants to be able to compare instances of `Deal` to check for equality,
    in order to remove duplicates from lists if any are found.

    She does not remember, *why* exactly she wanted this feature. Still, she
    insists it should be available.

    >>> deal_1 = Deal(symbol='msft', sticker_price=1, price=1)
    >>> deal_2 = Deal(symbol='msft', sticker_price=1, price=1)
    >>> deal_1 == deal_2
    True
    """

    def __eq__(self, other):
        if repr(other) != repr(self):
            return False
        return True

    def __lt__(self, other):
        return self.percent_of_sticker < other.percent_of_sticker

    @staticmethod
    def from_(company, Ticker=Ticker):
        deal = get_deal(company, Ticker=Ticker)
        return deal


class MockTicker:
    def __init__(self, symbol):
        price = 352.5 if symbol == "msft" else 98

        self.info = {
            "currentPrice": price
        }


def get_price(symbol, Ticker=Ticker):

    """
    >>> get_price("msft", Ticker=MockTicker)
    352.5
    >>> get_price([])
    {}
    >>> get_price(["msft"], Ticker=MockTicker)
    {'msft': 352.5}
    """

    if type(symbol) == str:
        price = Ticker(symbol).info["currentPrice"]
        return price

    prices = {
        the_symbol: get_price(the_symbol, Ticker=Ticker)
        for the_symbol in symbol
    }
    return prices

def get_percent_of_sticker(price, sticker_price):
    return int(100 * round(price/sticker_price, 2))

def get_deal(company, Ticker=Ticker):

    """
    >>> company = Company(symbol="msft", sticker_price=118)
    >>> deal = get_deal(company, Ticker=MockTicker)
    >>> deal
    Deal(symbol='msft', sticker_price=118, price=352.5, percent_of_sticker=299)
    """

    if isinstance(company, list):
        return get_deals(company, Ticker=Ticker)

    price = get_price(company.symbol, Ticker=Ticker)
    return Deal(
        symbol=company.symbol,
        sticker_price=company.sticker_price,
        price=price,
        percent_of_sticker=get_percent_of_sticker(price, company.sticker_price)
    )

def get_deals(companies, Ticker=Ticker):

    """
    >>> companies = [
    ...   Company("msft", 118),
    ...   Company("tsm", 22)
    ... ]
    >>> deals = get_deals(companies, Ticker=MockTicker)
    >>> deals[0]
    Deal(symbol='msft', sticker_price=118, price=352.5, percent_of_sticker=299)
    """

    sticker_prices = {
        company.symbol: company.sticker_price
        for company in companies
    }

    deals = []
    for symbol in sticker_prices.keys():
        price = get_price(symbol, Ticker=Ticker)
        sticker_price=sticker_prices[symbol]
        deals.append(
            Deal(symbol=symbol,
                 sticker_price=sticker_price,
                 price=price,
                 percent_of_sticker=get_percent_of_sticker(price, sticker_price)
            )
        )

    return sorted(deals)

def mock_get_sticker_price(symbol):
    class MockResponse:
        def json():
            return {"sticker_price": {"value": 22}}

    return MockResponse

@lru_cache
def get_sticker(symbol, api_host="143.42.16.225:8080", get=get):
    """
    >>> round(get_sticker("tsm", get=mock_get_sticker_price))
    22
    """
    url = f"http://{api_host}/search/{symbol}"
    result = get(url).json()["sticker_price"]["value"]
    return result

def round_sticker(sticker):

    """
    Prices above $2 should be rounded to the nearest integer.
    >>> round_sticker(22.01)
    22

    Prices below $2 should be rounded to full cents.
    >>> round_sticker(0.512)
    0.51
    """
    return round(sticker) if sticker >= 2 else round(sticker, 2)

def is_valid_sticker(result):
    return result is not None and result >= 0

def get_stickers(items):
    stickers = {}
    for key in items.keys():
        result = get_sticker(key)
        if is_valid_sticker(result):
            stickers[key] = round_sticker(result)
    return stickers

def with_preview(value):
    print(value)
    return value


class StickerPriceIngredients(NamedTuple):

    """
    >>> inputs = StickerPriceIngredients(
    ...     current_eps=1.31,
    ...     future_growth_rate_percent=15,
    ...     future_pe=30,
    ...     minimum_acceptable_rate_of_return_percent=15,
    ...     years=10
    ... )
    """

    current_eps: float
    future_growth_rate_percent: float
    future_pe: float
    minimum_acceptable_rate_of_return_percent: float
    years: int



class StickerPriceResults(NamedTuple):

    """
    Compare https://www.ruleoneinvesting.com/margin-of-safety-calculator/

    >>> outputs = StickerPriceResults(
    ...     future_eps=11,
    ...     future_value=254,
    ...     sticker_price=63,
    ...     mosp=31
    ... )
    >>> outputs.future_eps
    11
    """

    future_eps: float
    future_value: float
    sticker_price: float
    mosp: float

def get_sticker_price():

    """
    Expected results - not attained yet:

    >>> get_sticker_price().future_eps
    10.48

    Should be 11.

    >>> get_sticker_price().future_value
    314

    Should be 254.
    """

    ingredients = StickerPriceIngredients(
        current_eps=1.31,
        future_growth_rate_percent=15,
        future_pe=30,
        minimum_acceptable_rate_of_return_percent=15,
        years=10
    )

    years_to_double = 72 // ingredients.future_growth_rate_percent
    num_doubles = ingredients.years // years_to_double
    future_eps = 2 ** (1 + num_doubles) * ingredients.current_eps

    future_value = round(future_eps*ingredients.future_pe)

    results = StickerPriceResults(
        future_eps=future_eps,
        future_value=future_value,
        sticker_price=0,
        mosp=0
    )

    return results