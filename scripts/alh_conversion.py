"""
AUTHOR: JACQUELINE GARRAHAN
PYTHON: 3.x


This script is intended for the conversion of alhConfig files to phoebus alarm server xml configuration files.

See configuration file description for alh here: https://epics.anl.gov/EpicsDocumentation/ExtensionsManuals/AlarmHandler/alhUserGuide-1.2.35/ALHUserGuide.html#pgfId_689941
"""
import xml.etree.ElementTree as ET
import os
import copy
import fileinput
from treelib import Node, Tree


# TODO: ADD HANDLING OF SEVRCOMMAND, STATCOMMAND, BEEPSEVERITY, BEEPSEVR
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
        self.force_mask = force_mask
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
        self.count = None
        self.delay = None
        self.filename = ""


class InclusionMarker:
    node_children = None

    def __init__(self, name, filename):
        self.filename = filename
        self.name = name


class ALHFileParser:
    def __init__(self, filepath, config_name):
        self.filepath = filepath
        self.directory = "/".join(filepath.split("/")[:-1])
        self.filename = filepath.split("/")[-1]

        # current tracked item
        self._current_target = None

        # parent of current tracked item
        self._current_parent_group = None

        # for tracking items
        self.items = {}
        self.inclusions = {}

        self._inclusion_count = 0

        # create root node
        self.items[config_name] = AlarmNode(config_name)
        self._config_name = config_name

        # markers for tracking where at in parsing
        self._current_node = config_name
        self._current_path = config_name
        self._parent_path = None

    def parse_file(self):

        self._line_iterator = fileinput.input(self.filepath)

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

                elif split_line[0] == "$ALARMCOUNTFILTER":
                    self._process_alarm_count(split_line)

                else:
                    print("UNKNOWN ENTRY:")
                    print(next_line)

            next_line = next(self._line_iterator, None)

        return self.items

    def _process_group(self, split_line):

        # group name is stored as third element
        group_name = split_line[2]

        # parent is stored in second element
        parent = None
        if split_line[1] != "NULL":
            parent = split_line[1]

        # if this is not the top level of the file, store parent path and node path
        if parent:
            parent_path = f"{self._current_node}/{parent}"
            node_path = f"{self._current_node}/{parent}/{group_name}"

        # if no parent is specified, top level or downstream inclusion
        else:
            print(group_name)
            print(self._current_node)
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

        # update item and assign parent
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
        self.items[self._current_target].force_pv = ForcePV(
            force_mask, force_value, reset_value
        )

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
                        self.items[self._current_target].calcs[identifier] = next_split[
                            1
                        ]

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
                        self.items[self._current_target].guidance.append(
                            next_line.replace("\n", ",").strip()
                        )

        # if it is a single line guidance, will be a url reference
        else:
            urlname = split_line[1]
            self.items[self._current_target].guidance_url = urlname

    def _process_alias(self, split_line):
        self.items[self._current_target].alias = split_line[1]

    def _process_inclusion(self, split_line):
        parent = split_line[1]

        # HACK
        # TODO: Fix filepath handling
        include_filename = split_line[2]
        if include_filename[:2] == "./":
            include_filename = include_filename.replace(
                "./", "/Users/jgarra/sandbox/nalms-resources/examples/alh_files/"
            )

        # mark an inclusion with unique placeholder
        item_key = self._current_node + f"/INCLUDE_{self._inclusion_count}"
        self.items[item_key] = InclusionMarker(item_key, include_filename)
        self.items[self._current_target].add_child(item_key)
        self._inclusion_count += 1

        # track the inclusion for processing
        self.inclusions[item_key] = include_filename

    def _process_ackpv(self, split_line):
        """
        NOTE: This is currently unused in systems at SLAC
        """
        ack_pv_name = split_line[1]
        ack_value = split_line[2]

        # WRONG, CORRECT THE TARGET
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

        items[target] = HeartbeatPV(
            heartbeat_pv_name, seconds=seconds, value=heartbeat_val
        )

    def _process_alarm_count(self, split_line):
        items[self._current_target].count = split_line[1]
        items[self._current_target].delay = split_line[2]


class XMLBuilder:
    def __init__(self):
        self.groups = {}
        self.added_pvs = []
        self.settings_artifacts = []
        self._tree = None

    def build_tree(self, items, top_level_node):
        self._tree = Tree()

        self._configuration = ET.Element("config", name=top_level_node)
        self._config_name = top_level_node

        # create root node
        self._tree.create_node(
            top_level_node, top_level_node, data=items[top_level_node]
        )

        processed = []

        to_process = [top_level_node]

        while len(to_process) > 0:
            node = to_process.pop(0)
            children = items[node].node_children

            if children:
                for child in children:
                    self._tree.create_node(
                        items[child].name, child, parent=node, data=items[child]
                    )

                # add children to process
                to_process += children

        processed.append(node)

    def save_configuration(self, output_filename):
        root_node = self._tree.get_node(self._config_name)

        self._handle_children(root_node)

        with open(output_filename, "wb") as f:
            file_str = ET.tostring(self._configuration, encoding="utf8")
            f.write(file_str)

    def _handle_children(self, node, parent_group=None):
        children = self._tree.children(node.identifier)

        self._add_group(node.tag, node.data, parent_group=parent_group)

        if children:

            for child in children:
                if isinstance(child.data, AlarmLeaf):
                    self._add_pv(child.tag, node.tag, child.data)

                elif isinstance(child.data, AlarmNode):
                    self._handle_children(child, parent_group=node.tag)

                elif isinstance(child.data, InclusionMarker):
                    print("PROCESSING INCLUSION")
                    self._add_inclusion(node.tag, child.data.filename)

    def _add_group(self, group, data, parent_group=None):
        group_name = group
        if data.alias:
            group_name = data.alias

        if group not in self.groups:
            if not parent_group:
                self.groups[group] = ET.SubElement(
                    self._configuration, "component", name=group_name
                )
            else:
                self.groups[group] = ET.SubElement(
                    self.groups[parent_group], "component", name=group_name
                )

        # add guidance
        if data.guidance:
            guidance = ET.SubElement(self.groups[group], "guidance")
            guidance.text = " ".join(data.guidance)

        # add display url
        if data.guidance_url:
            display = ET.SubElement(self.groups[group], "display")
            display.text = data.guidance_url

        # add all commands
        if data.commands:
            for command in data.commands:
                command_item = ET.SubElement(self.groups[group], "command")
                command_item.text = command

        # TODO: sevr command and stat command automated actions

    def _add_pv(self, pvname, group, data):
        if pvname in self.added_pvs:
            pass

        else:
            self.added_pvs.append(pvname)
            pv = ET.SubElement(self.groups[group], "pv", name=pvname)
            enabled = ET.SubElement(pv, "enabled")
            enabled.text = "true"

            # disable latching by default
            latching = ET.SubElement(pv, "latching")
            latching.text = "false"

            if data.force_pv is not None:
                filter_pv = ET.SubElement(pv, "filter")
                filter_pv.text = self._process_forcepv(data.force_pv)

            # add guidance
            if data.guidance:
                guidance = ET.SubElement(pv, "guidance")
                guidance.text = " ".join(data.guidance)

            # add display url
            if data.guidance_url:
                display = ET.SubElement(pv, "display")
                display.text = data.guidance_url

            # add all commands
            if data.commands:
                for command in data.commands:
                    command_item = ET.SubElement(pv, "command")
                    command_item.text = command

            if data.description:
                decription = ET.SubElement(pv, "description")
                description.text = data.description

            # add count
            if data.count:
                count = ET.SubElement(pv, "count")
                count.text = data.count

            # add delay
            if data.delay:
                delay = ET.SubElement(pv, "delay")
                delay.text = data.delay

        # TODO: sevr command and stat command automated actions

    def _add_inclusion(self, group, filename):
        inclusion = ET.SubElement(
            self.groups[group],
            "xi:include",
            href=filename,
            xpointer="xpointer(/config/*",
            attrib={"xmlns:xi": "http://www.w3.org/2001/XInclude"},
        )

    def _process_forcepv(self, force_pv):
        text = force_pv.name
        if force_pv.is_calc:
            formatting = force_pv.calc_expressions.pop("A")

            for key, value in force_pv.calc_expressions.items():
                formatting.replace(key, value)

        if force_pv.force_value:
            text += f" != {force_pv.force_value}"

        return text


def convert_alh_to_phoebus(config_name, input_filename, output_filename):
    parser = ALHFileParser(input_filename, config_name)
    items = parser.parse_file()
    tree_builder = XMLBuilder()
    tree_builder.build_tree(items, config_name)
    tree_builder.save_configuration(output_filename)

    return True


if __name__ == "__main__":
    input_filename = (
        "/Users/jgarra/sandbox/nalms-resources/examples/alh_files/temp_li23.alhConfig"
    )
    output_filename = "/Users/jgarra/sandbox/nalms-resources/examples/test.xml"
    convert_alh_to_phoebus("test1", input_filename, output_filename)
