# Copyright Google Inc. 2017
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# https://github.com/GoogleCloudPlatform/bigquery-bokeh-dashboard/blob/master/dashboard/modules/base.py


class BaseModule:

    TOOLS = "pan,wheel_zoom,box_zoom,box_select,reset,save"

    def __init__(self, model=None):
        self.id = self.__module__
        self.model = model
        self.table = None

    def update_model(self, new_data):
        self.model.data_source.update(new_data)

    def update_selected(self, new_selected):
        self.model.data_source.selected.indices = [new_selected]

    def make_plot(self, *args, **kwargs):
        raise NotImplementedError

    def update_plot(self, *args, **kwargs):
        raise NotImplementedError

    def busy(self):
        raise NotImplementedError

    def unbusy(self):
        raise NotImplementedError
