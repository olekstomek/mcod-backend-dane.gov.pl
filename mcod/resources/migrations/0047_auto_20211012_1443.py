# Generated by Django 2.2.9 on 2021-10-12 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0046_auto_20211011_1618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='format',
            field=models.CharField(blank=True, choices=[('abw', 'ABW'), ('bat', 'BAT'), ('bmp', 'BMP'), ('csv', 'CSV'), ('dbf', 'DBF'), ('doc', 'DOC'), ('docx', 'DOCX'), ('dot', 'DOT'), ('epub', 'EPUB'), ('geojson', 'GEOJSON'), ('geotiff', 'GEOTIFF'), ('gif', 'GIF'), ('gpx', 'GPX'), ('grib', 'GRIB'), ('grib2', 'GRIB2'), ('htm', 'HTM'), ('html', 'HTML'), ('jpe', 'JPE'), ('jpeg', 'JPEG'), ('jpg', 'JPG'), ('json', 'JSON'), ('json-ld', 'JSON-LD'), ('jsonld', 'JSONLD'), ('kml', 'KML'), ('md', 'MD'), ('n3', 'N3'), ('nc', 'NC'), ('nquads', 'NQUADS'), ('nt', 'NT'), ('nt11', 'NT11'), ('ntriples', 'NTRIPLES'), ('odc', 'ODC'), ('odf', 'ODF'), ('odg', 'ODG'), ('odi', 'ODI'), ('odp', 'ODP'), ('ods', 'ODS'), ('odt', 'ODT'), ('pdf', 'PDF'), ('png', 'PNG'), ('pot', 'POT'), ('ppa', 'PPA'), ('ppm', 'PPM'), ('pps', 'PPS'), ('ppt', 'PPT'), ('pptx', 'PPTX'), ('ps', 'PS'), ('pwz', 'PWZ'), ('rd', 'RD'), ('rdf', 'RDF'), ('rtf', 'RTF'), ('shp', 'SHP'), ('svg', 'SVG'), ('tex', 'TEX'), ('texi', 'TEXI'), ('texinfo', 'TEXINFO'), ('tif', 'TIF'), ('tiff', 'TIFF'), ('trig', 'TRIG'), ('trix', 'TRIX'), ('tsv', 'TSV'), ('ttl', 'TTL'), ('turtle', 'TURTLE'), ('txt', 'TXT'), ('vsd', 'VSD'), ('webp', 'WEBP'), ('wiz', 'WIZ'), ('wsdl', 'WSDL'), ('xbm', 'XBM'), ('xlb', 'XLB'), ('xls', 'XLS'), ('xlsx', 'XLSX'), ('xml', 'XML'), ('xpdl', 'XPDL'), ('xsl', 'XSL')], max_length=150, null=True, verbose_name='Format'),
        ),
    ]
