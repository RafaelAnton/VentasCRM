# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta


def get_intervals_from_dates(start_date, end_date, interval_value,interval_option):
    """
    :param start_date: start date
    :param end_date: end date
    :param interval_value: interval value in integer
    :param interval_option: interval option days,month,week,etc..
    :return: list of dates
    """
    startdate = str(start_date)
    enddate = str(end_date)
    date_lists = []
    start = datetime.strptime(startdate, '%Y-%m-%d').date()
    end = datetime.strptime(enddate, '%Y-%m-%d').date()
    while start <= end:
        date_lists.append(start)
        if interval_option == 'days':
            start += relativedelta(days=interval_value)
        if interval_option == 'weeks':
            start += relativedelta(weeks=interval_value)
        if interval_option == 'months':
            start += relativedelta(months=interval_value)
        if interval_option == 'years':
            start += relativedelta(years=interval_value)
    return date_lists





