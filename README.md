# Wrapper Script for Publish CTData Datasets to CKAN

## Steps

1. Load datapackage.json
2. Create dict object to hold all required metadata fields
3. Extract data from datapackage.json and insert in correct places
4. Run validation tests on datapackages
5. Check if organization exists, and create if missing
6. Set dataset organization to the returned organization object
7. If resource exists, update, otherwise create
