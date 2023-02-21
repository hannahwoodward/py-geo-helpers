# py-geo-helpers

## EsgfRemoteResolver usage

- NB separate multiple values by comma e.g. 'variable': 'pr,prsn,tas'
- Query syntax: https://esgf.github.io/esg-search/ESGF_Search_RESTful_API.html#syntax
- You can first browse data on a node e.g. https://esgf-data.dkrz.de/projects/esgf-dkrz/
- List of ESGF nodes: https://esgf.llnl.gov/nodes.html

### CMIP6 example

```
query = {
  'experiment_id': 'ssp585',
  'frequency': 'mon',
  'grid_label': 'gn',
  'limit': 10,
  'mip_era': 'CMIP6',
  'source_id': 'UKESM1-0-LL',
  'table_id': 'SImon',
  'variable_id': 'siconc',
  'variant_label': 'r1i1p1f2'
}

resolver = EsgfRemoteResolver(
  query,
  base_url='https://esgf.ceda.ac.uk',
  download_url='https://esgf-index1.ceda.ac.uk',
  dry_run=False,
  local_path='_data/cmip6/UKESM1-0-LL/siconc',
)

resolver.load()
```


### CORDEX example

CORDEX requires openid authentication & project access:
- Create an openid account at https://esgf-data.dkrz.de
  - NB CEDA openid does not seem to work
- Request CORDEX access via https://esg-dn1.nsc.liu.se/ac/subscribe/CORDEX_Research/
  - You may be asked to log in with your openid details
  - You may need to visit this link twice to secure access

```
query = {
  'domain': 'EUR-11',
  'driving_model': 'MOHC-HadGEM2-ES',
  'experiment': 'rcp85',
  'limit': 1,
  'project': 'CORDEX',
  'time_frequency': 'mon',
  'variable': 'tas', 
  'start': '2010-01-01T00:00:00Z',
  'end': '2025-01-01T00:00:00Z'
}

resolver = EsgfRemoteResolver(
  query,
  dry_run=False,
  local_path='_data/cordex/EUR-11/tas',
  openid='https://esgf-data.dkrz.de/esgf-idp/openid/woodward',
  base_url='https://esgf-data.dkrz.de',
  download_url='https://esgf-data.dkrz.de'
)

resolver.load()
```
