# -*- coding: utf-8 -*-

"""
ckdata_ckan_publish.cli
-----------------------

Main `ctdata_ckan_publish` CLI.
"""

import json
import csv
import os
import re

import ckanapi
import click
import datapackage
import requests

source_lookup = {
    'uscensus': 'US Census',
    'ctsde': 'Connecticut State Department of Education',
    'ctdph': 'Connecticut Department of Public Health',
    'ctopm': 'Connecticut Office of Policy and Management',
    'samhsa': 'Substance Abuse and Mental Health Services Administration',
    'ctdmhas': 'Connecituct Department of Mental Health and Addiction Services',
    'municipalities': 'Municipalities',
    'ctdss': 'Connecticut Department of Social Services',
    'ctdol': 'Connecticut Department of Labor',
    'ctdecd': 'Connecticut Department of Economic and Community Development',
    'ctdcf': 'Connecticut Department of Children and Families',
    'ctocme': 'Connecticut Office of the Chief Medical Examiner',
    'ctoec': 'Connecticut Office of Early Childhood',
    'ctdespp': 'Connecticut Department of Emergency Services and Public Protections',
    'seda': 'Stanford Education Data Archive',
    'ctlib': 'Connecticut State Library',
    'cthfa': 'Connecticut Housing Finance Authority',
    'ctdot': 'Connecticut Department of Transportation',
    'ctdoh': 'Connecticut Department of Housing' }

 
regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def check_ckan_url(url):
    match = regex.match(url)
    if match:
        return True
    return False

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
    pkg = ckan.action.package_show(name_or_id=datapackage_json['name'])
    
    try:
        r_id = pkg['resources'][0]['id']
    except IndexError:
        r_id = None
    if r_id:
        try:
            ckan.action.resource_update(
                    id=r_id,
                    url='dummy-value',
                    name=datapackage_json['title'],
                    upload=open(resource_path, 'rb'))
        except Exception as e:
            raise e
    else:
        try:
            ckan.action.resource_create(
                    package_id=pkg['id'],
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
    extras.append({'key': 'Source', 'value': source_lookup[dp_json['sources'][0]['name']]})
    try:
        year_strs = [str(y) for y in dp_json['ckan_extras']['years_in_catalog']['value']]
        years = ';'.join(year_strs)
        extras.append({'key': 'Years in Catalog', 'value': years})
    except KeyError as e:
        raise e
    geo = dp_json['ckan_extras']['geography']['value']
    to_exclude = [geo, 'Year', 'FIPS', 'Value']
    for field in dp_json['resources'][0]['schema']['fields']:
        if field['dimension'] == False:
            continue
        extras.append({'key': field['name'], 'value': ';'.join(field['constraints']['enum'])})
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
@click.option('--ckan',
        help='URL for CKAN instance',
        envvar='CKANURL')
@click.option('--datapackage',
        help='A path to the datapackage.json',
        type=click.Path(exists=True))
@click.option('--ckanapikey', 
        default=None,
        help='You CKAN API key from your user account view',
        envvar='CKANAPIKEY')
@click.option('--dry',
        default=False,
        help='Do a dry run where everything is complete except for API calls')
def main(datapackage, ckanapikey, dry, ckan):
    """Main dispatcher function for publishing a dataset"""
    if check_ckan_url(ckan) is False:
        click.echo("{} isn't a valid url".format(ckan))
        raise TypeError
    datapackage_json, upload_object = load_datapackage_file(datapackage)
    ctdata = ckanapi.RemoteCKAN(ckan, apikey=ckanapikey, user_agent='CTData Publisher/1.0 (+http://ctdata.org)')
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

if __name__ == '__main__':
    main()
