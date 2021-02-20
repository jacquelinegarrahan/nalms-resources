"""
AUTHOR: JACQUELINE GARRAHAN
PYTHON: 3.x


This script is intended for the conversion of alhConfig files to phoebus alarm server xml configuration files.
"""
import xml.etree.ElementTree as ET
import os
import copy
from treelib import Node, Tree


# TODO: ADD HANDLING OF SEVRCOMMAND, STATCOMMAND, ALARMCOUNTERFILETER, BEEPSEVERITY, BEEPSEVR
# TODO: Fix path handling for include files

class HeartbeatPV:
    def __init__(self, name, value=None, seconds=None):
        self.name = name

class AckPV:
    def __init__(self, name, ack_value):
        self.name = name
        self.ack_value = ack_value

class SevrPV:
    def __init__(self, name):
        self.name = name

class ForcePV:
    def __init__(self, force_mask, force_value, reset_value):
        self.force_mask=force_mask
        self.force_value = force_value
        self.reset_value = reset_value
        self.name = None 
        self.is_calc = False
        self.calc_expressions = []
        self.base_calc = ""

    def add_calc(self, expression):
        self.calc_expressions.append(expression)

class AlarmNode:
    def __init__(self, group_name, filename=None):
        self.name = group_name
        self.alias = ""
        self.commands = []
        self.sevr_pv = None
        self.force_pv = None
        self.parent = None
        self.node_children = []
        self.guidance = []
        self.guidance_url = ""
        self.main_calc = ""
        self.calcs = {}
        self.filename = filename

    def add_child(self, child):
        if child in self.node_children:
            print(f"DUPLICATE CHILD FOR GROUP {self.name}: {child}")

        else:
            self.node_children.append(child)


class AlarmLeaf:
    node_children = None
    def __init__(self, channel_name, filename=None):
        self.name = channel_name
        self.mask = None
        self.alias = ""
        self.commands = []
        self.sevr_pv = None
        self.force_pv = None
        self.guidance = []
        self.guidance_url = []
        self.main_calc = ""
        self.calcs = {}
        self.filename = ""


class InclusionMarker():
    def __init__(self, filename):
        self.filename = filename


def build_tree(items, top_level_node):
    tree = Tree()

    # create root
    tree.create_node(top_level_node, top_level_node, data=items[top_level_node])
    processed = []

    to_process = [top_level_node]

    while len(to_process) > 0:
        node = to_process.pop(0)
        children = items[node].node_children

        if children:
            for child in children:
                tree.create_node(items[child].name, child, parent=node, data=items[child])

            # add children to process
            to_process += children
        
        processed.append(node)

    return tree


class ALHFileParser:

    def __init__(self, filepath):
        self.filepath = filepath
        self.directory = "/".join(filepath.split("/")[:-1])
        self.filename = filepath.split("/")[-1]

        # markers for tracking where at in parsing
        self._current_node = None
        self._current_path = None
        self._parent_path = None

        # current tracked item
        self._current_target = None

        # parent of current tracked item
        self._current_parent_group = None

        # for tracking items
        self.items = {}
        self.inclusions = {}

    def parse_file(self):

        with open(self.filepath) as f:
            self._line_iterator = f.readlines()
            
            next_line = next(self._line_iterator, None)

            while next_line:

                split_line = next_line.split()

                if len(split_line) > 0:

                    # process group entry
                    if split_line[0] == "GROUP":
                        self._process_group(split_line)

                    # process channel entry
                    elif split_line[0] == "CHANNEL":
                        self._process_channel(split_line)

                    # process command entry
                    elif split_line[0] == "$COMMAND":
                        self._process_command(split_line)

                    # process sevrpv command entry
                    elif split_line[0] == "$SEVRPV":
                        self._process_sevrpv(split_line)

                    # process forcepv command entry
                    elif split_line[0] == "$FORCEPV":
                        self._process_forcepv(split_line)

                    # process guidance entry
                    elif split_line[0] == "$GUIDANCE":
                        self._process_guidance(split_line)

                    # process alias entry
                    elif split_line[0] == "$ALIAS":
                        self._process_alias(split_line)

                    # process ackpv entry
                    elif split_line[0] == "$ACKPV":
                        self._process_ackpv(split_line)
                    
                    # skip comments
                    elif split_line[0][0] == "#":
                        pass

                    # process heartbeatpv
                    elif split_line[0] == "$HEARTBEATPV":
                        self._process_heartbeatpv(split_line)

                    elif split_line[0] == "INCLUDE":
                        self._process_inclusion(split_line)

                    else:
                        print("UNKNOWN ENTRY:")
                        print(next_line)

                next_line = next(self._line_iterator, None)

        return self.items

    def _process_group(self, split_line):

        # group name is stored as third element
        group_name = split_line[2]
        
        # store top level info
        if self._in_top_level:
            self._top_level_node = copy.copy(group_name)
            self._current_path = copy.copy(group_name)

        # parent is stored in second element
        parent = None
        if split_line[1] != "NULL":
            parent = split_line[1]

        # if this is not the top level of the file, store parent path and node path
        if not in_top_level:
            if parent:
                parent_path = f"{self._current_node}/{parent}"
                node_path = f"{self._current_node}/{parent}/{group_name}"
            
            # if no parent is specified, this is probably a downstream inclusion...
            else:
                parent_path = self._current_node
                node_path = f"{self._current_node}/{group_name}"

            # add to child to parent
            self.items[parent_path].add_child(node_path)

        # ad the node path to items and create node object
        if node_path not in self.items:
            self.items[node_path] = AlarmNode(group_name)

        # update target and parent group
        self._current_target = node_path
        self._current_parent_group = parent

    def _process_channel(self, split_line):

        # channel name is stored as the third element
        channel_name = split_line[2]

        # parent is stored as the second element
        parent = split_line[1]

        # if we currently have a defined parent group and this is different than the parent given
        # adjust path based on parent group and parent
        if self._current_parent_group and self._current_parent_group != parent:
            parent_path = f"{self._current_node}/{self._current_parent_group}/{parent}"
            node_path = f"{self._current_node}/{self._current_parent_group}/{parent}/{channel_name}"

        # otherwise, just use parent
        else:
            parent_path = f"{self._current_node}/{parent}"
            node_path = f"{self.current_node}/{parent}/{channel_name}"

        # update item and assign paretn
        self.items[node_path] = AlarmLeaf(channel_name, filename=filename)
        self.items[node_path].parent = parent_path

        # store parent node if it isn't in items
        if parent_path not in items:
            self.items[parent_path] = AlarmNode(parent, filename=filename)
            self.items[self._current_node].add_child(parent_path)

        # an optional mask is sometimes added as the fourth element
        if len(split_line) == 4:
            self.items[node_path].mask = split_line[3]

        # update current tracked item
        self._current_target = node_path

    def _process_command(self, split_line):
        command = " ".join(split_line[1:])
        # if multiple commands, break apart
        commands = command.split("!")
        # store commands on item as list of commands
        self.items[self._current_target].commands += commands

    def _process_sevrpv(self, split_line):
        self.items[self._current_target].sevr_pv = SevrPV(split_line[1])

    def _process_forcepv(self, split_line):
        # force mask is stored as the third entry
        force_mask = split_line[2]

        force_value = None
        reset_value = None

        # force value is stored as the fourth entry       
        if len(split_line) >= 4:
            force_value = split_line[3]

        # reset value is stored as the fifth entry
        if len(split_line) == 5:
            reset_value = split_line[4]

        # create a force pv for the item
        self.items[self._current_target].force_pv = ForcePV(force_mask, force_value, reset_value)

        # if this is a calc type force pv, mark as calc type
        if split_line[1] == "CALC":
            self.items[self._current_target].force_pv.is_calc = True

            # process following calc lines
            reached_end = False
            while not reached_end:
                next_line = next(self._line_iterator)
                if next_line:
                    next_split = next_line.split()

                    # get representative calculation
                    if next_split[0] == "FORCEPV_CALC":
                        self.items[self._current_target].main_calc = split_line[1]

                    # Force pvs use letter standins for complicated calcs, eg. FORCEPV_CALC_A
                    # Track these values
                    elif "FORCEPV_CALC_" in next_split[0]:
                        identifier = next_split[0][-1]
                        self.items[self._current_target].calcs[identifier] = next_split[1]

                    # otherwise have reached end
                    else:
                        reached_end = True
        
        # if not calc, name of the pv is the second element
        # update forcepv with the name of the forcepv
        else:
            force_pv_name = split_line[1]
            self.items[self._current_target].force_pv.name = force_pv_name

    def _process_guidance(self, split_line):

        # if this is a multiline guidance entry, collect all lines
        if len(split_line) == 1:

            reached_end = False
            while not reached_end:
                next_line = next(self._line_iterator)
                if next_line:
                    next_split = next_line.split()
                    if next_split[0] == "$END":
                        reached_end = True
                    else:
                        self.items[self._current_target].guidance.append(next_line)

        # if it is a single line guidance, will be a url reference
        else:
            urlname = split_line[1]
            self.items[self._current_target].guidance_url = urlname

    def _process_alias(self, split_line):
        self.items[self._current_target].alias = split_line[1]

    def _process_inclusion(self, split_line):
        parent = split_line[1]

        #HACK 
        #TODO: Fix filepath handling
        include_filename = split_line[2]
        if include_filename[:2] == "./":
            include_filename = include_filename.replace("./", "")

        # mark an inclusion with unique placeholder
        item_key = self._current_node + f"/INCLUDE{self._inclusion_count}"
        self.items[item_key] = InclusionMarker(include_filename)
        self._inclusion_count += 1

        # track the inclusion for processing
        self.inclusions[item_key] = include_filename

    def _process_ackpv(self, split_line):
        """
        NOTE: This is currently unused in systems at SLAC
        """
        ack_pv_name = split_line[1]
        ack_value = split_line[2]

        #WRONG, CORRECT THE TARGET
        items[self._current_target] = AckPV(ack_pv_name, ack_value)

    # FIX
    def _process_heartbeatpv(self, split_line):
        heartbeat_pv_name = split_line[1]
        
        heartbeat_val = None
        seconds = None
        if len(split_line) >= 3:
            heartbeat_val = split_line[2]

        if len(split_line) == 4:
            seconds = split_line[3]
        
        items[target] = HeartbeatPV(heartbeat_pv_name, seconds=seconds, value=heartbeat_val)

class XMLBuilder:
    def __init__(self, config_name, root):
        self.configuration = ET.Element("config", name=config_name)
        self.groups = {}
        self.added_pvs = []
        self.settings_artifacts = []

    def add_group(self, group, data, parent_group = None):
        group_name = group
        if data.alias:
            group_name = data.alias

        if group not in self.groups:
            if not parent_group:
                self.groups[group] = ET.SubElement(self.configuration, 'component', name=group_name)
            else:
                self.groups[group] = ET.SubElement(self.groups[parent_group], 'component', name=group_name)


    def add_pv(self, pvname, group, data):
        if pvname in self.added_pvs:
            pass

        else:
            self.added_pvs.append(pvname)
            pv = ET.SubElement(self.groups[group], "pv", name=pvname)
        #    description = ET.SubElement(pv, "description")
            enabled = ET.SubElement(pv, "enabled")
            enabled.text = 'true'

            if data.force_pv is not None:
                filter_pv = ET.SubElement(pv, "filter")
                filter_pv.text = self._process_forcepv(data.force_pv)


    def _process_forcepv(self, force_pv):

        text = force_pv.name
        if force_pv.is_calc:
            formatting = force_pv.calc_expressions.pop("A")

            for key, value in force_pv.calc_expressions.items():
                formatting.replace(key, value)

        if force_pv.force_value:
            text += f" != {force_pv.force_value}"

        return text
               
    

def handle_children(builder, tree, node, parent_group=None):
    children = tree.children(node.identifier)

    if children:
        builder.add_group(node.tag, node.data, parent_group=parent_group)

        for child in children:
            if isinstance(child.data, AlarmLeaf):
                builder.add_pv(child.tag, node.tag, child.data)

            elif isinstance(child.data, AlarmNode):
                handle_children(builder, tree, child, parent_group=node.tag)



def build_config_file(tree, config_name, output_filename):
    root = tree.root
    builder = XMLBuilder(config_name, root)
    root_node = tree.get_node(root)
    handle_children(builder, tree, root_node)

    with open (output_filename, "wb") as f : 
        file_str = ET.tostring(builder.configuration, encoding='utf8') 
        f.write(file_str)



def convert_alh_to_phoebus(input_filename, output_filename):
    config_name = output_filename.split("/")[-1].replace(".xml", "")
    items, top_level_node = parse_tree(input_filename)
    tree = build_tree(items, top_level_node)
    build_config_file(tree, config_name, output_filename)

    # while remaining inclusions
    # process next file

    return True

if __name__ == "__main__":
    input_filename = "/Users/jgarra/sandbox/nalms-resources/examples/alh_files/temp_li23_klys.alhConfig"
    output_filename = "/Users/jgarra/sandbox/nalms-resources/examples/test.xml"
    convert_alh_to_phoebus(input_filename, output_filename)
