# from django.shortcuts import render

# Create your views here.
from dal import autocomplete

from mcod.regions.api import PeliasApi


class RegionsAutocomplete(autocomplete.Select2ListView):

    def autocomplete_results(self, results):
        pelias = PeliasApi()
        results = pelias.autocomplete(self.q, layers='locality,localadmin')
        found_results = [(res["properties"]['gid'], res["properties"]["name"],)
                         for res in results['features']]
        return found_results

    def results(self, results):
        return [dict(id=x[0].split(':')[-1], text=x[1]) for x in results]
