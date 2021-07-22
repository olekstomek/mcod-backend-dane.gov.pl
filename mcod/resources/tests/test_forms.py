from django.utils.translation import gettext_lazy as _
from mcod.datasets.documents import Resource
from mcod.resources.forms import ChangeResourceForm


class TestChangeResourceForm:

    def test_maps_and_plots_correct_set(self, geo_tabular_data_resource):
        geo_tabular_data_resource.revalidate()
        rs = Resource.objects.get(pk=geo_tabular_data_resource.id)
        assert rs.tabular_data_schema
        data = rs.__dict__
        data.update({
            'dataset': rs.dataset_id,
            'geo_0': 'label',
            'geo_2': 'l',
            'geo_3': 'b'}
        )

        form = ChangeResourceForm(data=data, instance=rs)
        valid = form.is_valid()
        assert valid

    def test_map_and_plots_label_missing_for_coordinates(self, tabular_resource):
        tabular_resource.revalidate()
        rs = Resource.objects.get(pk=tabular_resource.id)
        assert rs.tabular_data_schema

        data = rs.__dict__
        data.update({
            'dataset': rs.dataset_id,
            'geo_1': 'l',
            'geo_2': 'b'
        })

        form = ChangeResourceForm(data=data, instance=rs)
        assert not form.is_valid()

        expected_message = _("Missing elements: {} for the map data set: {}.").format(
            _("label"), _('geographical coordinates'))
        expected_message += str(_(" Redefine the map by selecting the selected items."))

        assert expected_message in form.errors['maps_and_plots']

    def test_map_and_plots_label_missing_for_universal_address(self, tabular_resource):
        tabular_resource.revalidate()
        rs = Resource.objects.get(pk=tabular_resource.id)
        assert rs.tabular_data_schema
        data = rs.__dict__
        data.update({
            'dataset': rs.dataset_id,
            'geo_1': 'uaddress',
        })

        form = ChangeResourceForm(data=data, instance=rs)
        assert not form.is_valid()

        expected_message = _("Missing elements: {} for the map data set: {}.").format(
            _("label"),
            _('universal address'))
        expected_message += str(_(" Redefine the map by selecting the selected items."))
        assert expected_message in form.errors['maps_and_plots']

    def test_map_and_plots_label_missing_for_address(self, tabular_resource):
        tabular_resource.revalidate()
        rs = Resource.objects.get(pk=tabular_resource.id)
        assert rs.tabular_data_schema
        data = rs.__dict__
        data.update({
            'dataset': rs.dataset_id,
            'geo_1': 'place',
            'geo_2': 'postal_code'
        })

        form = ChangeResourceForm(data=data, instance=rs)
        assert not form.is_valid()

        expected_message = _("Missing elements: {} for the map data set: {}.").format(_("label"), _('address'))
        expected_message += str(_(" Redefine the map by selecting the selected items."))
        assert expected_message in form.errors['maps_and_plots']

    def test_map_and_plots_label_missing_only_label(self, tabular_resource):
        tabular_resource.revalidate()
        rs = Resource.objects.get(pk=tabular_resource.id)
        assert rs.tabular_data_schema
        data = rs.__dict__
        data.update({
            'dataset': rs.dataset_id,
            'geo_1': 'label',
        })

        form = ChangeResourceForm(data=data, instance=rs)
        assert not form.is_valid()
        assert (
            _("The map data set is incomplete.") in
            form.errors['maps_and_plots']
        )

    def test_map_and_plots_more_than_once(self, tabular_resource):
        tabular_resource.revalidate()
        rs = Resource.objects.get(pk=tabular_resource.id)
        assert rs.tabular_data_schema
        data = rs.__dict__
        data.update({
            'dataset': rs.dataset_id,
            'geo_1': 'label',
            'geo_2': 'label',
            'geo_3': 'b'
        })

        form = ChangeResourceForm(data=data, instance=rs)
        assert not form.is_valid()
        assert f'{_("element")} {_("label")} {_("occured more than once")}' in form.errors['maps_and_plots'][0]

    def test_map_and_plots_different_groups(self, tabular_resource):
        tabular_resource.revalidate()
        rs = Resource.objects.get(pk=tabular_resource.id)
        assert rs.tabular_data_schema

        data = rs.__dict__
        data.update({
            'dataset': rs.dataset_id,
            'geo_1': 'place',
            'geo_2': 'b'
        })

        form = ChangeResourceForm(data=data, instance=rs)
        assert not form.is_valid()
        assert (
            _("Selected items {} come from different map data sets.").format(f"{_('place')}, {_('b')}") in
            form.errors['maps_and_plots'][0] or
            _("Selected items {} come from different map data sets.").format(f"{_('b')}, {_('place')}") in
            form.errors['maps_and_plots'][0]
        )
