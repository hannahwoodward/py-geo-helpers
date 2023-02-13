from datetime import datetime
from pathlib import Path
from pyesgf.logon import LogonManager
# from utils import test_date_bounds
import aiohttp
import asyncio
import json
import urllib
import shutil
import ssl

class EsgfRemoteResolver():
    def __init__(
        self,
        query,
        base_url='https://esgf.ceda.ac.uk',
        download_url='https://esgf-index1.ceda.ac.uk',
        dry_run=False,
        local_path='',
        openid=None
    ):
        '''
        TODO
        Class EsgfRemoteResolver:
            query e.g. {
                'experiment',
                'source',
                'variable',
                'frequency'
                'grid_label'
                'table_id'
                'variant_label'
            }
            local_path: str or False

        Notes:
        - You can browse data via website on a node, e.g.
          https://esgf-data.dkrz.de/projects/esgf-dkrz/
        - CORDEX requires openid authentication & project access
        - Create an openid account via https://esgf-data.dkrz.de
          - NB CEDA openid does not seem to work
        - Request CORDEX access via https://esg-dn1.nsc.liu.se/ac/subscribe/CORDEX_Research/
          - You may be asked to log in with your openid details
          - You may need to visit this link twice to secure access

        Local path examples:
            '{project}/{domain}/{driving_model}/{self.variable_id}'

        Links:
        - nodes: https://esgf.llnl.gov/nodes.html
        - query syntax: https://esgf.github.io/esg-search/ESGF_Search_RESTful_API.html#syntax

        '''
        self.query = query
        self.base_url = base_url
        self.download_url = download_url
        self.dry_run = dry_run
        self.local_path = local_path
        self.openid = openid
        self.ssl_context = None
        self.filepaths = []

    def load(self):
        '''
        TODO
        '''
        self.openid != None and self.esgf_login()

        results = self.query_datasets()
        if len(results) == 0:
            print('No results found, exiting.')
            return []

        print('Results:')
        self.filepaths = [self.download_dataset_files(item) for item in results]

        return self.filepaths

    def query_datasets(self):
        '''
        TODO
        '''
        query = {
            'format': 'application/solr+json',
            'latest': 'true',
            'limit': 20,
            'offset': 0,
            'replica': 'false',
            'type': 'Dataset',
        } | self.query

        url = f'{self.base_url}/esg-search/search/?{urllib.parse.urlencode(query)}'
        print('Querying datasets:', f'-> {url}', sep='\n')
        try:
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)

            response_json = json.load(response)['response']
            print('Total results from ESGF: ' + str(response_json['numFound']))

            return response_json['docs']
        except Exception as e:
            print('An error occurred during initial query', e, sep='\n')

            return []

    async def download_dataset_files(self, item):
        '''
        TODO
        '''
        item_id = item['id']
        item_index_node = item['index_node']
        url = f'{self.download_url}/search_files/{item_id}/{item_index_node}/?limit=1000' # TODO: pagination

        print('-> -> Requesting remote file URLs for dataset:', f'-> -> {url}', sep='\n')
        try:
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)

            results = json.load(response)['response']['docs']
        except Exception as e:
            print('An error occurred during second query', e, sep='\n')

            return []

        local_filenames = []
        for item in results:
            file_url = [url.split('|')[0] for url in item['url'] if 'HTTPServer' in url]
            if len(file_url) == 0:
                continue

            file_url = file_url[0]
            filename = urllib.parse.urlparse(file_url).path.split('/')[-1]

            # TODO: test filename for start/end in self.query
            # *daterange_from_filename(filename)

            # TODO: replace local_path with params
            local_filename = Path(self.local_path, filename)
            local_filename.parent.mkdir(parents=True, exist_ok=True)

            if local_filename.exists():
                print(f'-> -> -> Already exists, skipping: {local_filename}')
                local_filenames.append(str(local_filename))
                continue

            if self.dry_run:
                print(f'-> -> -> DRY RUN, skipping: {local_filename}')
                continue

            print(f'-> -> -> Downloading:')
            print(f'-> -> -> {file_url}')
            print(f'-> -> -> {local_filename}')

            try:
                await self.fetch_esgf_file(file_url, local_filename, ssl=self.ssl_context)

                local_filenames.append(str(local_filename))
            except Exception as e:
                # TODO: improve error messaging, change to aiohttp for status codes?
                print('-> -> ->', 'Error')
                print('-> -> ->', e)
                if hasattr(e, 'status_code') and e.status_code in [401, 402, 403]:
                    print('-> -> ->', 'Have you passed in `openid`?')

        return local_filenames

    def esgf_login(self):
        '''
        TODO
        '''
        lm = LogonManager()
        lm.logoff() # TODO: needed?
        lm.logon_with_openid(
            openid=self.openid,
            password=None,
            interactive=True,
            bootstrap=True
        )

        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        ssl_context.load_verify_locations(capath=lm.esgf_certs_dir)
        ssl_context.load_cert_chain(lm.esgf_credentials)

        self.ssl_context = ssl_context

    async def fetch_esgf_file(self, url, local, ssl=None):
        async def fetch(url, local, ssl):
            with aiohttp.ClientSession(trust_env=True) as client:
                with client.request('get', url, ssl=ssl) as response:
                    assert response.status == 200

                    chunk_size = 2048
                    with open(local, 'wb') as fd:
                        for chunk in response.content.iter_chunked(chunk_size):
                            fd.write(chunk)

        loop = asyncio.get_event_loop()
        loop.create_task(fetch(url, local, ssl=ssl))

    # def filter_result(x):
    #     date_out_of_bounds = test_date_bounds(
    #         time_slice,
    #         *daterange_from_filename(filename)
    #     )
    #     return date_out_of_bounds
