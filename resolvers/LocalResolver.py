from pathlib import Path
import xarray

class LocalResolver():
    def __init__(
        filepaths
    ):
        self.filepaths = filepaths

    def load(self):
        for path in self.filepaths:
            if not Path(path).exists():
                print('Error 404', f'-> {path}', sep='\n')
                return None

        data = xarray.open_mfdataset(
            paths=self.filepaths,
            combine='by_coords',
            use_cftime=True
        )

        return data
