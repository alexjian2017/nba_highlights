def date_converter(date: str) -> str:
    """
    input: NOV 03, 2023
    output: 2023-11-03
    """
    month_str = ['jan', 'feb', 'mar', 'apr', 'may',
                 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    month_converter = {month: f'{i:02.0f}' for month,
                       i in zip(month_str, range(1, 13))}
    month, day, year = date.strip().split()
    month = month_converter[month.lower()]
    day = day[:-1]
    return f'{year}-{month}-{day}'


print(date_converter('jan 31, 2023'))
