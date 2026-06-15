from .registry import register

import pandas as pd
import io

@register("ihtar_cekme")
def agent_ihtar_cekme(self, df_json):
    df = pd.read_json(io.StringIO(df_json), orient='records')
    
    required_columns = []
    empty_rows = df[required_columns].isnull().any(axis=1)
    if empty_rows.any():
        self.task.status = "rejected"
        self.task.save()
        self.task.delete()
        return

    self.task.status = "in_progress"
    self.task.save()

    previous_progress = 0
    for index,row in df.iterrows():
        print(row)