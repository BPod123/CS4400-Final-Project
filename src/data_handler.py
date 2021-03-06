from bisect import bisect_left
from random import sample
import pandas as pd
from numpy import array




def treat_attr_as_null(value):
    return value is None or str(value) in {"", "- na -", "nan"}


def get_row_form_table(row_index, table):
    return {key: table[key][row_index] for key in table.keys()}


def generate_examples(training_data, ltable, rtable, class_name):
    examples = []
    labels = []
    for i in range(len(training_data)):
        l_id, r_id, label = training_data["ltable_id"][i], training_data["rtable_id"][i], training_data[class_name][i]
        examples.append(get_data_from_ids(l_id, r_id, ltable, rtable))
        labels.append(label)
    examples, labels = array(examples), array(labels)
    return examples, labels






def get_data_from_ids(left_id, right_id, ltable, rtable, class_name = None, label=None):
    """

    :param left_id: row of the left table with all of the information related to the item
    :param right_id: row of the right table with all of the information related to the item
    :param ltable: Dataframe
    :param rtable: Dataframe
    :return: data: dict containing the extrapolated data
    """
    left_index = bisect_left(ltable["id"], left_id)
    right_index = bisect_left(ltable["id"], right_id)
    left_data = {key: ltable[key][left_index] for key in ltable}
    right_data = {key: rtable[key][right_index] for key in rtable}
    data = extrapolate_attributes(left_data, right_data)
    if class_name is not None:
        data[class_name] = label
    return data


def extrapolate_attributes(left_data: dict, right_data: dict):
    """
    :param left_data:  Row from left table
    :param right_data: Row from right table
    :return: price difference if both prices are listed, else, -1
    """


    if not treat_attr_as_null(left_data["price"]) and not treat_attr_as_null(right_data["price"]):
        price_diff = abs(left_data["price"] - right_data["price"]) / ((left_data["price"] + right_data["price"]) / 2.0)
    else:
        price_diff = -1
    return array([price_diff])


def split_table(table: pd.DataFrame, percentage: float, random=True):
    """
    Divides a dataframe into two tables. This is used for splitting the training dataset into a
    training dataset and a validation dataset
    :param table: pd.DataFrame
    :param percentage: The percent of the table to that will be in the first (left) return item
    :param random if true, will take the values from different parts of a table so that the result will be different
        every run
    :return: table1, table2 where table1 has percentage of the data from table
    """
    left_num_items = int(percentage * len(table))
    if random:
        left_indices = set(sample(range(len(table)), left_num_items))
    else:
        left_indices = set(range(left_num_items))
    right_indicecs = set(range(len(table))).difference(left_indices)
    dicts = []
    for indices in [left_indices, right_indicecs]:
        table_dict = {"ltable_id": [], "rtable_id": [], "label": []}
        for i in indices:
            table_dict["ltable_id"].append(table["ltable_id"][i])
            table_dict["rtable_id"].append(table["rtable_id"][i])
            table_dict["label"].append(table["label"][i])
        dicts.append(table_dict)
    ltable = pd.DataFrame(data=dicts[0])
    rtable = pd.DataFrame(data=dicts[1])
    return ltable, rtable


def trim_tables(train: pd.DataFrame, ltable: pd.DataFrame, rtable: pd.DataFrame):
    """
    Removes rows from ltable, rtable that are not used in the training data.
    Will also reformat training data so that the new indices are correct.
    :param train: Training DataFrame
    :param ltable: left table DataFrame
    :param rtable: right table DataFrame
    :return: formatted train, ltable, and rtable
    """
    left_ids_to_keep = list({x for x in train["ltable_id"]})
    right_ids_to_keep = list({x for x in train["rtable_id"]})
    ltable_dict, rtable_dict = dict(), dict()
    trimed_lr_tables = []
    id_maps = []
    # Remove non-training rows from ltable and rtable
    for table_dict, table, ids_to_keep in [(ltable_dict, ltable, left_ids_to_keep),
                                           (rtable_dict, rtable, right_ids_to_keep)]:
        ids_to_keep.sort()
        id_maps.append({ids_to_keep[i]: i for i in range(len(ids_to_keep))})
        for key in table.keys():
            table_dict[key] = [table[key][i] for i in ids_to_keep]

        trimed_lr_tables.append(pd.DataFrame(data=table_dict))

    trimed_ltable, trimed_rtable = trimed_lr_tables[0], trimed_lr_tables[1]
    # Recreate training data with renumbered ids
    left_id_map, right_id_map = id_maps[0], id_maps[1]
    new_training_dict = {"ltable_id": [], "rtable_id": [], "label": []}
    for i in range(len(train)):
        l_id = train["ltable_id"][i]
        r_id = train["rtable_id"][i]
        label = train["label"][i]
        new_l_id = left_id_map[l_id]
        new_r_id = right_id_map[r_id]
        new_training_dict["ltable_id"].append(new_l_id)
        new_training_dict["rtable_id"].append(new_r_id)
        new_training_dict["label"].append(label)
    reformatted_training_data = pd.DataFrame(data=new_training_dict)
    return reformatted_training_data, trimed_ltable, trimed_rtable