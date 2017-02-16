# Dataset publishing CLI for CTData CKAN datasets
#
import ckanapi
import csv
import json
import click
import datapackage
import requests
import os

def create(upload_object, ckan, apikey): 
    id = ckan.action.package_show(name_or_id=upload_object['name'])['id']
    upload_object['id'] = id
    headers = {'user-agent': 'ctdata-publisher/0.0.1', 'Authorization': apikey, 'Content-Type': 'charset=utf-8'}
    try:
        r = requests.post('http://data.ctdata.org/api/action/package_patch', headers=headers, data = json.dumps(upload_object))
    except Exception as e:
        raise e

def upload_resource(datapackage_json, ckan, rootpath):
    resource_path = os.path.join(os.getcwd(), rootpath, datapackage_json['resources'][0]['path'])
    click.echo(resource_path)

    r_id = ckan.action.package_show(name_or_id=datapackage_json['name'])['resources'][0]['id']

    try:
        ckan.action.resource_update(
                id=r_id,
                url='dummy-value',
                name=datapackage_json['title'],
                upload=open(resource_path, 'rb'))
    except Exception as e:
        raise e

def get_extras_object(dp_json):
    extras_to_exclude = ['years_in_catalog', 'expected_number_of_geographies', 'default']
    extras = [{'key': e['ckan_name'], 'value': e['value']} for k,e in dp_json['ckan_extras'].items() if k not in extras_to_exclude]  
    extras.append({'key': 'Description', 'value': dp_json['description']})
    extras.append({'key': 'Default', 'value': json.dumps(dp_json['ckan_extras']['default']['value'])})
    try:
        years = ';'.join(dp_json['ckan_extras']['years_in_catalog']['value'])
        extras.append({'key': 'Years in Catalog', 'value': years})
    except KeyError as e:
        raise e
    geo = dp_json['ckan_extras']['geography']['value']
    to_exclude = [geo, 'Year', 'FIPS', 'Value']
    for field in dp_json['resources'][0]['schema']['fields']:
        if field['dimension'] == False:
            continue
        extras.append({'key': field['name'], 'value': ','.join(field['constraints']['enum'])})
    return extras

def load_datapackage_file(datapackage_path):
    dp = datapackage.DataPackage(datapackage_path)
    dpdict = dp.descriptor
    try:
        upload_object = {'name': dpdict['name'], 'title': dpdict['title'], 'maintainer': dpdict['author']['name'], 
                'maintainer_email': dpdict['author']['email'], 'owner_org': dpdict['sources'][0]['name']}
    except KeyError as e:
        raise e
    try:
        dp.validate()
    except datapackage.exceptions.ValidationError as e: 
        if e.instance == dpdict['author']:
            pass
        else:
            raise e
    try:
        upload_object['extras'] = get_extras_object(dpdict)
    except (KeyError, Exception) as e:
        raise e
    return dpdict, upload_object

@click.command()
@click.option('--datapackage', help='A path to the datapackage.json', type=click.Path(exists=True))
@click.option('--ckanapikey', default=None, help='You CKAN API key from your user account view', envvar='CKANAPIKEY')
@click.option('--dry', default=False, help='Do a dry run where everything is complete except for API calls')
@click.option('--verbose', default=False)
def process(datapackage, ckanapikey, dry, verbose):
    """Main dispatcher function for publishing a dataset"""
    datapackage_json, upload_object = load_datapackage_file(datapackage)
    ctdata = ckanapi.RemoteCKAN('http://data.ctdata.org', apikey=ckanapikey, user_agent='CTData Publisher/1.0 (+http://ctdata.org)')
    package_root_dir = datapackage.split('/')[0]
    if not dry:
        # First we will create the new dataset or overwrite the existing dataset 
        try:
            create(upload_object, ctdata, ckanapikey)
        except Exception as e:
            raise e 
        click.echo("{} Created".format(upload_object['title']))
        
        # Then we will upload the resource
        try:
            upload_resource(datapackage_json, ctdata, package_root_dir)
        except Exception as e:
            raise e

        click.echo("{} Uploaded".format(datapackage_json['resources'][0]['path']))
    # else: 
    #     click.echo("DRY RUN---{} Created".format(upload_object['title']))
    #     click.echo("DRY RUN---{} Uploaded".format(datapackage_json['resources'][0]['path']))
    # if (verbose and dry) or verbose:
    #     click.echo(json.dumps(upload_object))

if __name__ == '__main__':
    process()
