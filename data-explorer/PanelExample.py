#!/usr/bin/env python

import param
import pandas as pd
import panel as pn
import hvplot.pandas
import datetime as dt
from bokeh.settings import settings

from google.cloud import firestore
from astropy import units as u

pn.extension()
firestore_db = firestore.Client()

settings.resources = 'cdn'
settings.resources = 'inline'

stats_rows = [d.to_dict() 
              for d 
              in firestore_db.collection('stats').where('year', '>=', 2018).stream()]
stats_df = pd.DataFrame(stats_rows)

# Better format for exptime
exptime_hours = [round(x, 2) 
                 for x 
                 in (stats_df.total_minutes_exptime * u.minute).values.to(u.hour).value]
stats_df['total_hours_exptime'] = exptime_hours
stats_df.index = pd.to_datetime(stats_df.year.astype(str) + stats_df.week.map(lambda x: f'{x:02d}') + ' SUN', format='%Y%W %a')

# Reorder
cols = ['unit_id', 
        'week', 
        'year', 
        'num_images', 
        'num_observations', 
        'total_minutes_exptime', 
        'total_hours_exptime',
       ]
stats_df = stats_df.reindex(columns=cols)

# Get a full index (e.g. zeros for weeks with no stats)
stats_df = stats_df.sort_index().drop(columns=['week', 'year'])

def reindex_by_date(group):
    dates = pd.date_range(group.index.min(), group.index.max(), freq='W')
    unit_id = group.iloc[0].unit_id
    group = group.reindex(dates).fillna(0)
    group.unit_id = unit_id
    
    return group

stats_df = stats_df.groupby(['unit_id']).apply(reindex_by_date).droplevel(0)

stats_df['year'] = stats_df.index.year
stats_df['week'] = stats_df.index.week
stats_df = stats_df.reset_index(drop=True)

stats_df = stats_df.sort_index()
stats_df.tail(10)


# In[3]:


units = ['The whole world! 🌎', 'PAN001', 'PAN006', 'PAN008', 'PAN010', 'PAN012', 'PAN018']


# In[4]:


start_date = dt.datetime.strptime('2018-01-01', '%Y-%M-%d')
end_date = dt.datetime.now()

class ObservationsExplorer(param.Parameterized):
    """Param interace for inspecting observations"""
    ra = param.Range(doc='RA [degrees]', default=(20, 30), bounds=(-180, 180), label='RA [deg]')
    dec = param.Range(doc='Dec [degrees]', default=(30, 40), bounds=(-90, 90), label='Dec [deg]')
    time = param.DateRange(label='Date Range', default=(start_date, end_date), bounds=(start_date, end_date))
    min_num_images = param.Integer(doc='Minimum number of images', default=10, bounds=(1, 50))
    field_name = param.String(doc='Field name')
    unit_id = param.ListSelector(doc='Unit IDs', label='Unit IDs')
    
    df = param.DataFrame(precedence=-1)
    
    def plot(self):
        return 


# In[5]:


obs_explorer = ObservationsExplorer()


# In[6]:


# Set the unit_ids (these would come from the db normally)
obs_explorer.params('unit_id').objects = units
obs_explorer.params('unit_id').default = units[0:1]


# In[7]:


limit = 100


# In[20]:


welcome = pn.panel(f'''
Recent Observations

Showing the {limit} most recent observations.
''')


# In[21]:


recent_tab = pn.Column(
    welcome,
    name='Recent',
)


# In[22]:


comet = '☄'
black_star = '★'
white_star = '☆'

search_tab = pn.Column(
    pn.Param(obs_explorer.param,
        widgets={
            'unit_id': pn.widgets.MultiChoice,
            'min_num_images': pn.widgets.IntSlider,
            'field_name': {
                'type': pn.widgets.TextInput, 
                'placeholder': 'Leave blank for best results'
            }
        }
    ),
    pn.widgets.Button(
        name=f'{black_star} ¡Search the stars! {black_star}',
        button_type='success'
    ),
    name='Search',
)


# In[23]:


sidebar = pn.WidgetBox(
    pn.Tabs(
        recent_tab,
        search_tab,        
    )
)


# In[24]:


main_app = pn.panel(
    pn.Row(
        sidebar,
        stats_df.hvplot.table()
    ),
    name='main_app'
)


# In[ ]:


main_app.show()

