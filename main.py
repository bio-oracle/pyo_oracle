import pyo_oracle

result = pyo_oracle.list_layers(variables={"chl", "o2"}, ssp=("ssp585"), time_period="present", depth="surf", dataframe=False)
print(result)
