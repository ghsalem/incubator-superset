import datetime
import json
import os
import random

import pandas as pd
from sqlalchemy import Date, Float, String

from superset import db
from superset.utils import core as utils
from .helpers import (
    config,
    Dash,
    DATA_FOLDER,
    get_slice_json,
    merge_slice,
    Slice,
    TBL,
    update_slice_ids,
)


def load_unicode_test_data():
    """Loading unicode test dataset from a csv file in the repo"""
    df = pd.read_csv(os.path.join(DATA_FOLDER, 'unicode_utf8_unixnl_test.csv'),
                     encoding='utf-8')
    # generate date/numeric data
    df['dttm'] = datetime.datetime.now().date()
    df['value'] = [random.randint(1, 100) for _ in range(len(df))]
    df.to_sql(  # pylint: disable=no-member
        'unicode_test',
        db.engine,
        if_exists='replace',
        chunksize=500,
        dtype={
            'phrase': String(500),
            'short_phrase': String(10),
            'with_missing': String(100),
            'dttm': Date(),
            'value': Float(),
        },
        index=False)
    print('Done loading table!')
    print('-' * 80)

    print('Creating table [unicode_test] reference')
    obj = db.session.query(TBL).filter_by(table_name='unicode_test').first()
    if not obj:
        obj = TBL(table_name='unicode_test')
    obj.main_dttm_col = 'dttm'
    obj.database = utils.get_or_create_main_db()
    db.session.merge(obj)
    db.session.commit()
    obj.fetch_metadata()
    tbl = obj

    slice_data = {
        'granularity_sqla': 'dttm',
        'groupby': [],
        'metric': 'sum__value',
        'row_limit': config.get('ROW_LIMIT'),
        'since': '100 years ago',
        'until': 'now',
        'where': '',
        'viz_type': 'word_cloud',
        'size_from': '10',
        'series': 'short_phrase',
        'size_to': '70',
        'rotation': 'square',
        'limit': '100',
    }

    print('Creating a slice')
    slc = Slice(
        slice_name='Unicode Cloud',
        viz_type='word_cloud',
        datasource_type='table',
        datasource_id=tbl.id,
        params=get_slice_json(slice_data),
    )
    merge_slice(slc)

    print('Creating a dashboard')
    dash = (
        db.session.query(Dash)
        .filter_by(dashboard_title='Unicode Test')
        .first()
    )

    if not dash:
        dash = Dash()
    js = """\
{
    "CHART-Hkx6154FEm": {
        "children": [],
        "id": "CHART-Hkx6154FEm",
        "meta": {
            "chartId": 2225,
            "height": 30,
            "sliceName": "slice 1",
            "width": 4
        },
        "type": "CHART"
    },
    "GRID_ID": {
        "children": [
            "ROW-SyT19EFEQ"
        ],
        "id": "GRID_ID",
        "type": "GRID"
    },
    "ROOT_ID": {
        "children": [
            "GRID_ID"
        ],
        "id": "ROOT_ID",
        "type": "ROOT"
    },
    "ROW-SyT19EFEQ": {
        "children": [
            "CHART-Hkx6154FEm"
        ],
        "id": "ROW-SyT19EFEQ",
        "meta": {
            "background": "BACKGROUND_TRANSPARENT"
        },
        "type": "ROW"
    },
    "DASHBOARD_VERSION_KEY": "v2"
}
    """
    dash.dashboard_title = 'Unicode Test'
    pos = json.loads(js)
    update_slice_ids(pos, [slc])
    dash.position_json = json.dumps(pos, indent=4)
    dash.slug = 'unicode-test'
    dash.slices = [slc]
    db.session.merge(dash)
    db.session.commit()
