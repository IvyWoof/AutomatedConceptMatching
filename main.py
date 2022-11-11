from configparser import ConfigParser

import numpy as np
import sqlalchemy
from bs4 import BeautifulSoup
import pandas as pd
import sqlalchemy as db
from fuzzywuzzy import fuzz, process


def read_mimosa_xml(engine):
    i = 1
    name_list = []
    description_list = []
    relationship_list = []
    id_list = []

    with open("standards_files/mimosa_standards.xsd") as fp:
        soup = BeautifulSoup(fp, "xml")

    for concept_name in soup.find_all("complexType", {'name': True}):
        if concept_name is not None:
            name_list.append(concept_name['name'])

    # Removes duplicates from list
    name_list = list(dict.fromkeys(name_list))

    # Finds and appends concept description to list
    for stored_name in name_list:
        for complex_type in soup.find_all('xs:complexType', {'name': stored_name}):
            complex_description = complex_type.find('xs:documentation')
            if complex_description is not None:
                description_value = complex_description.get_text()
                description_list.append(description_value)
            else:
                #append concept name to missing description
                description_list.append('N/A')

    for stored_name in name_list:
        list_length = len(name_list)
        for complex_type in soup.find_all('xs:complexType', {'name': stored_name}):
            headers = [tag['type'] for tag in complex_type.find_all("xs:element", {'type': True})]
            if not headers:
                relationship_list.append(['N/A'])
            else:
                relationship_list.append(headers)

        list2 = [x for x in relationship_list if x != []]

        while i <= list_length:
            id_list.append(i)
            i += 1

    # Write name and description to df
    csv_list = {'idMimosa': id_list, 'name': name_list, 'description': description_list, 'relationships': list2}
    mimosa_df = pd.DataFrame(csv_list)
    mimosa_df['relationships'] = mimosa_df['relationships'].str.join(', ')
    mimosa_df.to_sql('mimosa', con=engine, if_exists='replace', chunksize=1000, index=False)
    print('----mimosa table created----')

    return mimosa_df


def read_plcs_xml(engine):
    i = 1
    id_list = []
    name_list = []
    description_list = []
    relationship_list = []

    # Opens mimosa xsd file
    with open("standards_files/plcs_standards.xsd") as fp:
        soup = BeautifulSoup(fp, "xml")

    # Finds concept names in xml file
    for concept_name in soup.find_all("complexType", {'name': True}):
        if concept_name is not None:
            name_list.append(concept_name['name'])

    # Removes duplicates from list.
    name_list = list(dict.fromkeys(name_list))

    # Finds and appends concept description to list.
    for stored_name in name_list:
        list_length = len(name_list)
        for complex_type in soup.find_all('xsd:complexType', {'name': stored_name}):
            complex_description = complex_type.find('xsd:documentation')
            if complex_description is not None:
                description_value = complex_description.get_text()
                description_list.append(description_value)
            else:
                description_list.append('N/A')

        for complex_type in soup.find_all('xsd:complexType', {'name': stored_name}):
            headers = [tag['type'] for tag in complex_type.find_all("xsd:element", {'type': True})]
            if not headers:
                relationship_list.append(['N/A'])
            else:
                relationship_list.append(headers)

            list2 = [x for x in relationship_list if x != []]

        while i <= list_length:
            id_list.append(i)
            i += 1

    # Write name and description to df
    df_list = {'idPLCS': id_list, 'name_plcs': name_list, 'description': description_list, 'relationships': list2}
    plcs_df = pd.DataFrame(df_list)
    plcs_df['relationships'] = plcs_df['relationships'].str.join(', ')
    plcs_df.to_sql('plcs', con=engine, if_exists='replace', chunksize=1000, index=False)
    print('----plcs table created----')

    return plcs_df


def connect_to_db():
    meta = db.MetaData()
    user_info = config_object["SQLSERVERCONFIG"]
    engine = db.create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
                           .format(user=format(user_info["user"]),
                                   pw=format(user_info["password"]),
                                   db=format(user_info["database"])))
    print('----Connected to DB----')

    mimosa = db.Table(
        'mimosa',
        meta,
        db.Column('id_mimosa', db.Integer, primary_key=True),
        db.Column('name', db.String(256)),
        db.Column('description', db.String(5000)),
        db.Column('relationships', db.String(5000)),
    )

    plcs = db.Table(
        'plcs',
        meta,
        db.Column('id_plcs', db.Integer, primary_key=True),
        db.Column('name', db.String(256)),
        db.Column('description', db.String(5000)),
        db.Column('relationships', db.String(5000)),
    )

    similarity = db.Table(
        'similarity',
        meta,
        db.Column('id_sim', db.Integer, primary_key=True),
        db.Column('name_plcs', db.String(256)),
        db.Column('name_mimosa', db.String(256)),
        db.Column('sim_name', db.Integer),
        db.Column('sim_description', db.Integer),
        db.Column('sim_relationship', db.Integer),
    )

    meta.create_all(engine)
    print("Tables were created")
    return engine


def name_match(dfm, dfp):
    threshold = 0
    mlist = []
    plist = []
    slist = []
    id_list = []
    unique_id = 0

    plcs_name_list = dfp['name_plcs'].values.tolist()
    mimosa_name_list = dfm['name'].values.tolist()
    for name_compare_plcs in plcs_name_list:
        for name_compare_mimosa in mimosa_name_list:
            similarity_score = fuzz.token_set_ratio(name_compare_mimosa, name_compare_plcs)
            if similarity_score >= threshold:
                mlist.append(name_compare_mimosa)
                plist.append(name_compare_plcs)
                slist.append(similarity_score)
                unique_id += 1
                id_list.append(unique_id)

    df_list = {'id_sim': id_list, 'name_plcs': plist, 'name_mimosa': mlist, 'sim_name': slist}
    sim_df = pd.DataFrame(df_list)
    return sim_df


def description_matching(dfm, dfp, df):
    s_description = []
    mimosa_matching_description = []
    plcs_matching_description = []

    test = dfp['description'].values.tolist()
    test2 = dfm['description'].values.tolist()
    for potential in test:
        for example in test2:
            if example == 'N/A':
                s_description.append(0)
            else:
                similarity = fuzz.ratio(example, potential)
                s_description.append(similarity)

    df2 = df.assign(sim_description=s_description)
    print('----description done----')
    return df2


def relationship_matching(dfm, dfp, df2):
    t1_simlist = []

    test = dfp['relationships'].values.tolist()
    test2 = dfm['relationships'].values.tolist()
    test3 = [w.replace('N/A', '') for w in test]
    test4 = [w.replace('N/A', '') for w in test2]
    for potential in test3:
        for example in test4:
            similarity = fuzz.token_set_ratio(example, potential)
            t1_simlist.append(similarity)

    df3 = df2.assign(sim_relationships=t1_simlist)
    df3.to_sql('similarity', con=engine, if_exists='replace', chunksize=1000, index=False)
    print('----relationships done----')
    return df3

def createConfig():
    # Get the configparser object
    config_object = ConfigParser()

    # Assume we need 2 sections in the config file, let's call them USERINFO and SERVERCONFIG
    config_object["THRESHOLDANDWEIGHTING"] = {
        "Threshold": "40",
        "Name Weighting": "65",
        "Description Weighting": "23",
        "Relationship Weighting": "12"
    }

    config_object["SQLSERVERCONFIG"] = {
        "User": "root",
        "Password": "alanna1",
        "Database": "automatedmatching"
    }

    # Write the above sections to config.ini file
    with open('config.ini', 'w') as conf:
        config_object.write(conf)

    # Read config.ini file
    config_object = ConfigParser()
    config_object.read("config.ini")

    return config_object

def weighting(df3):
    user_info = config_object["THRESHOLDANDWEIGHTING"]
    name_weighting = float(user_info["name weighting"])
    description_weighting = float(user_info["description weighting"])
    relationship_weighting = float(user_info["relationship weighting"])
    threshold = float(user_info["threshold"])

    df3["weighted_similarity"] = df3["sim_name"] * name_weighting / 100 + df3["sim_description"] * description_weighting / 100 + df3["sim_relationships"] * relationship_weighting /100
    df3 = df3[df3.weighted_similarity >= threshold]

    df3.to_sql('similarity', con=engine, if_exists='replace', chunksize=1000, index=False)


config_object = createConfig()
engine = connect_to_db()
mimosa_df = read_mimosa_xml(engine)
plcs_df = read_plcs_xml(engine)
sim_df = name_match(mimosa_df, plcs_df)
df2 = description_matching(mimosa_df, plcs_df, sim_df)
df3 = relationship_matching(mimosa_df, plcs_df, df2)
weighting(df3)

