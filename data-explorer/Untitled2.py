#!/usr/bin/env python
# coding: utf-8

# In[1]:


import param
import pandas as pd
import panel as pn
import hvplot.pandas
import datetime as dt

pn.extension()


# In[2]:


units = ['The whole world! 🌎', 'PAN001', 'PAN006', 'PAN008', 'PAN010', 'PAN012', 'PAN018']


# In[3]:


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


# In[4]:


obs_explorer = ObservationsExplorer()


# In[5]:


# Set the unit_ids (these would come from the db normally)
obs_explorer.params('unit_id').objects = units
obs_explorer.params('unit_id').default = units[0:1]


# In[6]:


limit = 100


# In[7]:


welcome = pn.panel(f'''
## Recent Observations

Showing the {limit} most recent observations.
''')


# In[8]:


recent_tab = pn.Column(
    welcome,
    name='Recent',
)


# In[9]:


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


# In[13]:


sidebar = pn.WidgetBox(
    pn.Tabs(
        recent_tab,
        search_tab,        
    ),
    height=800
)


app = pn.panel(
    sidebar,
)


app.show()
