# Copyright 2019-2020 the openage authors. See copying.md for legal info.


from ...dataformat.converter_object import ConverterObject,\
    ConverterObjectGroup
from enum import Enum


class GenieUnitObject(ConverterObject):
    """
    Ingame object in AoE2.
    """

    def __init__(self, unit_id, full_data_set, members=None):
        """
        Creates a new Genie unit object.

        :param unit_id: The internal unit_id of the unit.
        :param full_data_set: GenieObjectContainer instance that
                              contains all relevant data for the conversion
                              process.
        :param members: An already existing member dict.
        """

        super().__init__(unit_id, members=members)

        self.data = full_data_set

    def __repr__(self):
        return "GenieUnitObject<%s>" % (self.get_id())


class GenieGameEntityGroup(ConverterObjectGroup):
    """
    A collection of GenieUnitObject types that form an "upgrade line"
    in Age of Empires. This acts as the common super class for
    units and buildings.

    The first unit in the line will become the GameEntity, the rest will
    be patches to that GameEntity applied by Techs.
    """

    def __init__(self, line_id, full_data_set):
        """
        Creates a new Genie game entity line.

        :param line_id: Internal line obj_id in the .dat file.
        :param full_data_set: GenieObjectContainer instance that
                              contains all relevant data for the conversion
                              process.
        """

        super().__init__(line_id)

        # Reference to everything else in the gamedata
        self.data = full_data_set

        # The line is stored as an ordered list of GenieUnitObjects.
        self.line = []

        # This dict stores unit ids and their repective position in the
        # unit line for quick referencing and searching
        self.line_positions = {}

        # List of units/buildings that the line can create
        self.creates = []

        # List of GenieTechEffectBundleGroup objects
        self.researches = []

        # List of units that the line can garrison
        self.garrison_entities = []

        # List of units/buildings where the line can garrison
        self.garrison_locations = []

    def add_creatable(self, line):
        """
        Adds another line to the list of creatables.

        :param line: The GenieBuildingLineGroup the villager produces.
        """
        if not self.contains_creatable(line.get_head_unit_id()):
            self.creates.append(line)

    def add_researchable(self, tech_group):
        """
        Adds a tech group to the list of researchables.

        :param tech_group: The GenieTechLineGroup the building researches.
        """
        if not self.contains_researchable(tech_group.get_id()):
            self.researches.append(tech_group)

    def add_unit(self, genie_unit, position=-1, after=None):
        """
        Adds a unit/building to the line.

        :param genie_unit: A GenieUnit object that is part of this
                           line.
        :param position: Puts the unit at an specific position in the line.
                         If this is -1, the unit is placed at the end 
        :param after: ID of a unit after which the new unit is
                      placed in the line. If a unit with this obj_id
                      is not present, the unit is appended at the end
                      of the line.
        """
        unit_id = genie_unit.get_member("id0").get_value()

        # Only add unit if it is not already in the list
        if not self.contains_unit(unit_id):
            insert_index = len(self.line)

            if position > -1:
                insert_index = position

                for unit in self.line_positions.keys():
                    if self.line_positions[unit] >= insert_index:
                        self.line_positions[unit] += 1

            elif after:
                if self.contains_unit(after):
                    insert_index = self.line_positions[after] + 1

                    for unit in self.line_positions.keys():
                        if self.line_positions[unit] >= insert_index:
                            self.line_positions[unit] += 1

            self.line_positions.update({genie_unit.get_id(): insert_index})
            self.line.insert(insert_index, genie_unit)

    def contains_creatable(self, line_id):
        """
        Returns True if a line with line_id is a creatable of
        this unit.
        """
        if isinstance(self, GenieUnitLineGroup):
            line = self.data.building_lines[line_id]

        elif isinstance(self, GenieBuildingLineGroup):
            line = self.data.unit_lines[line_id]

        return line in self.creates

    def contains_entity(self, unit_id):
        """
        Returns True if a entity with unit_id is part of the line.
        """
        return unit_id in self.line_positions.keys()

    def contains_researchable(self, line_id):
        """
        Returns True if a tech line with line_id is researchable
        in this building.
        """
        tech_line = self.data.tech_groups[line_id]

        return tech_line in self.researches

    def has_armor(self, armor_class):
        """
        Checks if units in the line have a specific armor class.

        :param armor_class: The type of armor class searched for.
        :type armor_class: int
        :returns: True if the train location obj_id is greater than zero.
        """
        head_unit = self.get_head_unit()
        armors = head_unit.get_member("armors").get_value()
        for armor in armors.values():
            type_id = armor.get_value()["type_id"].get_value()

            if type_id == armor_class:
                return True

        return False

    def has_attack(self, armor_class):
        """
        Checks if units in the line can execute a specific command.

        :param armor_class: The type of attack class searched for.
        :type armor_class: int
        :returns: True if the train location obj_id is greater than zero.
        """
        head_unit = self.get_head_unit()
        attacks = head_unit.get_member("attacks").get_value()
        for attack in attacks.values():
            type_id = attack.get_value()["type_id"].get_value()

            if type_id == armor_class:
                return True

        return False

    def has_command(self, command_id):
        """
        Checks if units in the line can execute a specific command.

        :param command_id: The type of command searched for.
        :type command_id: int
        :returns: True if the train location obj_id is greater than zero.
        """
        head_unit = self.get_head_unit()
        commands = head_unit.get_member("unit_commands").get_value()
        for command in commands:
            type_id = command.get_value()["type"].get_value()

            if type_id == command_id:
                return True

        return False

    def has_projectile(self, projectile_id):
        """
        Checks if units shoot a projectile with this ID.

        :param projectile_id: The ID of the projectile unit.
        :type projectile_id: int
        :returns: True if the train location obj_id is greater than zero.
        """
        head_unit = self.get_head_unit()
        projectile_id_0 = head_unit.get_member("attack_projectile_primary_unit_id").get_value()
        projectile_id_1 = head_unit.get_member("attack_projectile_secondary_unit_id").get_value()

        return (projectile_id_0 == projectile_id or projectile_id_1 == projectile_id)

    def is_creatable(self):
        """
        Units/Buildings are creatable if they have a valid train location.

        :returns: True if the train location obj_id is greater than zero.
        """
        # Get the train location obj_id for the first unit in the line
        head_unit = self.get_head_unit()
        train_location_id = head_unit.get_member("train_location_id").get_value()

        # -1 = no train location
        return train_location_id > -1

    def is_harvestable(self):
        """
        Checks whether the group holds any of the 4 main resources Food,
        Wood, Gold and Stone.

        :returns: True if the group contains at least one resource storage.
        """
        head_unit = self.get_head_unit()
        for resource_storage in head_unit.get_member("resource_storage").get_value():
            type_id = resource_storage.get_value()["type"].get_value()

            if type_id in (0, 1, 2, 3, 15, 16, 17):
                return True

        return False

    def is_garrison(self):
        """
        Checks whether the group can garrison other entities. This covers
        all of these garrisons:

        - Natural garrisons (castle, town center, tower)
        - Production garrisons (barracks, archery range, stable, etc.)
        - Unit garrisons (ram, siege tower)
        - Transport ships

        This does not include kidnapping units!

        :returns: True if the group falls into the above categories.
        """
        head_unit = self.get_head_unit()
        trait = head_unit.get_member("trait").get_value()

        # Transport ship/ram
        if trait & 0x01:
            return True

        # Production garrison
        type_id = head_unit.get_member("unit_type").get_value()
        if len(self.creates) > 0 and type_id == 80:
            return True

        # Natural garrison
        if head_unit.has_member("garrison_type"):
            garrison_type = head_unit.get_member("garrison_type").get_value()

            if garrison_type > 0:
                return True

        return False

    def is_gatherer(self):
        """
        Checks whether the group has any gather abilities.

        :returns: True if the group contains at least one resource storage.
        """
        return self.has_command(5)

    def is_passable(self):
        """
        Checks whether the group has a passable hitbox.

        :returns: True if the group has obstruction type 0.
        """
        head_unit = self.get_head_unit()
        return head_unit.get_member("obstruction_type").get_value() == 0

    def is_projectile_shooter(self):
        """
        Units/Buildings are projectile shooters if they have assigned a projectile ID.

        :returns: True if one of the projectile IDs is greater than zero.
        """
        # Get the projectiles' obj_id for the first unit in the line. AoE's
        # units stay ranged with upgrades, so this should be fine.
        head_unit = self.get_head_unit()
        projectile_id_0 = head_unit.get_member("attack_projectile_primary_unit_id").get_value()
        projectile_id_1 = head_unit.get_member("attack_projectile_secondary_unit_id").get_value()

        # -1 -> no projectile
        return (projectile_id_0 > -1 or projectile_id_1 > -1)

    def is_ranged(self):
        """
        Groups are ranged if their maximum range is greater than 0.

        :returns: True if the group's max range is greater than 0.
        """
        head_unit = self.get_head_unit()
        return head_unit["weapon_range_max"].get_value() > 0

    def is_melee(self):
        """
        Groups are melee if they have a Combat ability and are not ranged units.

        :returns: True if the group is not ranged and has a combat ability.
        """
        return self.has_command(7)

    def is_repairable(self):
        """
        Only certain lines and classes are repairable.

        :returns: True if the group's class is repairable.
        """
        return self.get_class_id() in (2, 13, 20, 21, 22, 53)

    def is_unique(self):
        """
        Groups are unique if they belong to a specific civ.

        :returns: True if the group is tied to one specific civ.
        """
        # Get the enabling research obj_id for the first unit in the line
        head_unit = self.get_head_unit()
        head_unit_id = head_unit.get_member("id0").get_value()

        if isinstance(self, GenieUnitLineGroup):
            if head_unit_id in self.data.unit_connections.keys():
                head_unit_connection = self.data.unit_connections[head_unit_id]

            else:
                # Animals
                return False

        elif isinstance(self, GenieBuildingLineGroup):
            head_unit_connection = self.data.building_connections[head_unit_id]

        enabling_research_id = head_unit_connection.get_member("enabling_research").get_value()

        # does not need to be enabled -> not unique
        if enabling_research_id == -1:
            return False

        # Get enabling civ
        enabling_research = self.data.genie_techs[enabling_research_id]
        enabling_civ_id = enabling_research.get_member("civilization_id").get_value()

        # Enabling tech has no specific civ -> not unique
        return enabling_civ_id > -1

    def get_class_id(self):
        """
        Return the class ID for units in the group.
        """
        return self.get_head_unit().get_member("unit_class").get_value()

    def get_garrison_mode(self):
        """
        Returns the mode the garrison operates in. This is used by the
        converter to determine which storage abilities the line will get.

        :returns: The garrison mode of the line.
        :rtype: GenieGarrisonMode
        """
        head_unit = self.get_head_unit()
        trait = head_unit.get_member("trait").get_value()

        # Ram
        if trait == 1:
            return GenieGarrisonMode.UNIT_GARRISON

        # Transport ship
        if trait == 3:
            return GenieGarrisonMode.TRANSPORT

        # Natural garrison
        if head_unit.has_member("garrison_type"):
            garrison_type = head_unit.get_member("garrison_type").get_value()

            if garrison_type > 0:
                return GenieGarrisonMode.NATURAL

        # Production garrison
        type_id = head_unit.get_member("unit_type").get_value()
        if len(self.creates) > 0 and type_id == 80:
            return GenieGarrisonMode.SELF_PRODUCED

        return None

    def get_head_unit_id(self):
        """
        Return the obj_id of the first unit in the line.
        """
        head_unit = self.get_head_unit()
        return head_unit.get_member("id0").get_value()

    def get_head_unit(self):
        """
        Return the first unit in the line.
        """
        return self.line[0]

    def get_unit_position(self, unit_id):
        """
        Return the position of a unit in the line.
        """
        return self.line_positions[unit_id]

    def get_train_location_id(self):
        """
        Returns the group_id for building line if the unit is
        creatable, otherwise return None.
        """
        if self.is_creatable():
            head_unit = self.get_head_unit()
            return head_unit.get_member("train_location_id").get_value()

        return None

    def __repr__(self):
        return "GenieGameEntityGroup<%s>" % (self.get_id())


class GenieUnitLineGroup(GenieGameEntityGroup):
    """
    A collection of GenieUnitObject types that form an "upgrade line"
    in Age of Empires.

    Example: Spearman->Pikeman->Helbardier

    The first unit in the line will become the GameEntity, the rest will
    be patches to that GameEntity applied by Techs.
    """

    def contains_unit(self, unit_id):
        """
        Returns True if a unit with unit_id is part of the line.
        """
        return self.contains_entity(unit_id)

    def get_civ_id(self):
        """
        Returns the enabling civ obj_id if the unit is unique,
        otherwise return None.
        """
        if self.is_unique():
            head_unit = self.get_head_unit()
            head_unit_id = head_unit.get_member("id0").get_value()
            head_unit_connection = self.data.unit_connections[head_unit_id]
            enabling_research_id = head_unit_connection.get_member("enabling_research").get_value()

            enabling_research = self.data.genie_techs[enabling_research_id]
            return enabling_research.get_member("civilization_id").get_value()

        return None

    def __repr__(self):
        return "GenieUnitLineGroup<%s>" % (self.get_id())


class GenieBuildingLineGroup(GenieGameEntityGroup):
    """
    A collection of GenieUnitObject types that represent a building
    in Age of Empires. Buildings actually have no line obj_id, so we take
    the obj_id of the first occurence of the building's obj_id as the line obj_id.

    Example1: Blacksmith(feudal)->Blacksmith(castle)->Blacksmith(imp)

    Example2: WatchTower->GuardTower->Keep

    Buildings in AoE2 also create units and research techs, so
    this is handled in here.

    The 'head unit' of a building line becomes the GameEntity, the rest will
    be patches to that GameEntity applied by Techs.
    """

    def __init__(self, line_id, full_data_set):
        super().__init__(line_id, full_data_set)

        # IDs of resources that cen be dropped off here
        self.accepts_resources = set()

        # Unit lines that this building trades with
        self.trades_with = []

    def add_accepted_resource(self, resource_id):
        """
        Adds a resourced that can be dropped off at this building.

        :param resource_id: ID of the resource that can be dropped off.
        """
        self.accepts_resources.add(resource_id)

    def add_trading_line(self, unit_line):
        """
        Adds a reference to a line that trades with this building.

        :param unit_line: Line that trades with this building.
        """
        self.trades_with.append(unit_line)

    def contains_unit(self, building_id):
        """
        Returns True if a building with building_id is part of the line.
        """
        return self.contains_entity(building_id)

    def has_foundation(self):
        """
        Returns True if the building has a foundation terrain.
        """
        head_unit = self.get_head_unit()
        return head_unit["foundation_terrain_id"].get_value() > -1

    def is_dropsite(self):
        """
        Returns True if the building accepts resources.
        """
        return len(self.accepts_resources) > 0

    def is_trade_post(self):
        """
        Returns True if the building is traded with.
        """
        return len(self.trades_with) > 0

    def get_accepted_resources(self):
        """
        Returns resource IDs for resources that can be dropped off at this building.
        """
        return self.accepts_resources

    def __repr__(self):
        return "GenieBuildingLineGroup<%s>" % (self.get_id())


class GenieStackBuildingGroup(GenieBuildingLineGroup):
    """
    Buildings that stack with other units and have annexes. These buildings
    are replaced by their stack unit once built.

    Examples: Gate, Town Center

    The 'stack unit' becomes the GameEntity, the 'head unit' will be a state
    during construction.
    """

    def __init__(self, stack_unit_id, head_building_id, full_data_set):
        """
        Creates a new Genie building line.

        :param stack_unit_id: "Actual" building that appears when constructed.
        :param head_building_id: The building used during construction.
        :param full_data_set: GenieObjectContainer instance that
                              contains all relevant data for the conversion
                              process.
        """
        super().__init__(stack_unit_id, full_data_set)

        self.head = self.data.genie_units[head_building_id]
        self.stack = self.data.genie_units[stack_unit_id]

    def is_creatable(self):
        """
        Stack buildings are created through their head building. We have to
        lookup its values.

        :returns: True if the train location obj_id is greater than zero.
        """
        train_location_id = self.head.get_member("train_location_id").get_value()

        # -1 = no train location
        if train_location_id == -1:
            return False

        return True

    def is_gate(self):
        """
        Checks if the building has gate properties.

        :returns: True if the building has obstruction class 4.
        """
        head_unit = self.get_head_unit()
        return head_unit.get_member("obstruction_class").get_value() == 4

    def get_head_unit(self):
        """
        Return the first unit in the line.
        """
        return self.head

    def get_stack_unit(self):
        """
        Returns the unit that is stacked on this building after construction.
        """
        return self.stack

    def get_head_unit_id(self):
        """
        Returns the stack unit ID because that is the unit that is referenced by other entities.
        """
        return self.get_stack_unit_id()

    def get_stack_unit_id(self):
        """
        Returns the stack unit ID.
        """
        return self.stack.get_member("id0").get_value()

    def get_train_location_id(self):
        """
        Stack buildings are creatable when their head building is creatable.

        Returns the group_id for a villager group if the head building is
        creatable, otherwise return None.
        """
        if self.is_creatable():
            return self.head.get_member("train_location_id").get_value()

        return None

    def __repr__(self):
        return "GenieStackBuildingGroup<%s>" % (self.get_id())


class GenieUnitTransformGroup(GenieUnitLineGroup):
    """
    Collection of genie units that reference each other with their
    transform_id.

    Example: Trebuchet
    """

    def __init__(self, line_id, head_unit_id, full_data_set):
        """
        Creates a new Genie transform group.

        :param head_unit_id: Internal unit obj_id of the unit that should be
                             the initial state.
        :param full_data_set: GenieObjectContainer instance that
                              contains all relevant data for the conversion
                              process.
        """

        super().__init__(line_id, full_data_set)

        self.head_unit = self.data.genie_units[head_unit_id]

        transform_id = self.head_unit.get_member("transform_unit_id").get_value()
        self.transform_unit = self.data.genie_units[transform_id]

    def is_projectile_shooter(self):
        """
        Transform groups are projectile shooters if their head or transform units
        have assigned a projectile ID.

        :returns: True if one of the projectile IDs is greater than zero.
        """
        projectile_id_0 = self.head_unit.get_member("attack_projectile_primary_unit_id").get_value()
        projectile_id_1 = self.head_unit.get_member("attack_projectile_secondary_unit_id").get_value()
        projectile_id_2 = self.transform_unit.get_member("attack_projectile_primary_unit_id").get_value()
        projectile_id_3 = self.transform_unit.get_member("attack_projectile_secondary_unit_id").get_value()

        # -1 -> no projectile
        return (projectile_id_0 > -1 or projectile_id_1 > -1
                or projectile_id_2 > -1 or projectile_id_3 > -1)

    def get_head_unit_id(self):
        """
        Returns the unit that is switched to when picking up something.
        """
        return self.head_unit["id0"].get_value()

    def get_head_unit(self):
        """
        Returns the unit that is switched to when picking up something.
        """
        return self.head_unit

    def get_transform_unit(self):
        """
        Returns the unit that is switched to when picking up something.
        """
        return self.transform_unit

    def __repr__(self):
        return "GenieUnitTransformGroup<%s>" % (self.get_id())


class GenieMonkGroup(GenieUnitLineGroup):
    """
    Collection of monk and monk with relic. The switch
    is hardcoded in AoE2. (Missionaries are handled as normal lines
    because they cannot pick up relics).

    The 'head unit' will become the GameEntity, the 'switch unit'
    will become a Container ability with CarryProgress.
    """

    def __init__(self, line_id, head_unit_id, switch_unit_id, full_data_set):
        """
        Creates a new Genie monk group.

        :param head_unit_id: The unit with this task will become the actual
                             GameEntity.
        :param switch_unit_id: This unit will be used to determine the
                               CarryProgress objects.
        :param full_data_set: GenieObjectContainer instance that
                              contains all relevant data for the conversion
                              process.
        """
        super().__init__(line_id, full_data_set)

        self.head_unit = self.data.genie_units[head_unit_id]
        self.switch_unit = self.data.genie_units[switch_unit_id]

    def is_garrison(self):
        return True

    def get_garrison_mode(self):
        return GenieGarrisonMode.MONK

    def get_switch_unit(self):
        """
        Returns the unit that is switched to when picking up something.
        """
        return self.switch_unit

    def __repr__(self):
        return "GenieMonkGroup<%s>" % (self.get_id())


class GenieAmbientGroup(GenieGameEntityGroup):
    """
    One Genie unit that is an ambient scenery object.
    Mostly for resources, specifically trees. For these objects
    every frame in their graphics file is a variant.

    Example: Trees, Gold mines, Sign
    """

    def contains_unit(self, ambient_id):
        """
        Returns True if the ambient object with ambient_id is in this group.
        """
        return self.contains_entity(ambient_id)

    def is_projectile_shooter(self):
        return False

    def __repr__(self):
        return "GenieAmbientGroup<%s>" % (self.get_id())


class GenieVariantGroup(GenieGameEntityGroup):
    """
    Collection of multiple Genie units that are variants of the same game entity.
    Mostly for cliffs and ambient terrain objects.

    Example: Cliffs, flowers, mountains
    """

    def contains_unit(self, object_id):
        """
        Returns True if a unit with unit_id is part of the group.
        """
        return self.contains_entity(object_id)

    def __repr__(self):
        return "GenieVariantGroup<%s>" % (self.get_id())


class GenieUnitTaskGroup(GenieUnitLineGroup):
    """
    Collection of genie units that have the same task group.

    Example: Male Villager, Female Villager

    The 'head unit' of a task group becomes the GameEntity, all
    the other are used to create more abilities with AnimationOverride.
    """

    # From unit connection
    male_line_id = 83   # male villager (with combat task)

    # Female villagers have no line obj_id, so we use the combat unit
    female_line_id = 293  # female villager (with combat task)

    def __init__(self, line_id, task_group_id, full_data_set):
        """
        Creates a new Genie task group.

        :param task_group_id: Internal task group obj_id in the .dat file.
        :param head_task_id: The unit with this task will become the head unit.
        :param full_data_set: GenieObjectContainer instance that
                              contains all relevant data for the conversion
                              process.
        """

        super().__init__(line_id, full_data_set)

        self.task_group_id = task_group_id

    def add_unit(self, genie_unit, position=-1, after=None):
        # Force the idle/combat units at the beginning of the line
        if genie_unit.get_member("id0").get_value() in (GenieUnitTaskGroup.male_line_id,
                                                        GenieUnitTaskGroup.female_line_id):
            super().add_unit(genie_unit, 0, after)

        else:
            super().add_unit(genie_unit, position, after)

    def is_creatable(self):
        """
        Task groups are creatable if any unit in the group is creatable.

        :returns: True if any train location obj_id is greater than zero.
        """
        for unit in self.line:
            train_location_id = unit.get_member("train_location_id").get_value()
            # -1 = no train location
            if train_location_id > -1:
                return True

        return False

    def get_train_location_id(self):
        """
        Returns the group_id for building line if the task group is
        creatable, otherwise return None.
        """
        for unit in self.line:
            train_location_id = unit.get_member("train_location_id").get_value()
            # -1 = no train location
            if train_location_id > -1:
                return train_location_id

        return None

    def __repr__(self):
        return "GenieUnitTaskGroup<%s>" % (self.get_id())


class GenieVillagerGroup(GenieUnitLineGroup):
    """
    Special collection of task groups for villagers.

    Villagers come in two task groups (male/female) and will form
    variants of the common villager game entity.
    """

    valid_switch_tasks_lookup = {
        5: "GATHER",    # Gather from resource spots
        7: "COMBAT",    # Attack
        101: "BUILD",   # Build buildings
        106: "REPAIR",  # Repair buildings, ships, rams
        110: "HUNT",    # Kill first, then gather
    }

    def __init__(self, group_id, task_group_ids, full_data_set):
        """
        Creates a new Genie villager group.

        :param group_id: Unit obj_id for the villager unit that is referenced by buildings
                         (in AoE2: 118 = male builder).
        :param task_group_ids: Internal task group ids in the .dat file.
                               (as a list of integers)
        :param full_data_set: GenieObjectContainer instance that
                              contains all relevant data for the conversion
                              process.
        """
        super().__init__(group_id, full_data_set)

        self.data = full_data_set

        # Reference to the variant task groups
        self.variants = []
        for task_group_id in task_group_ids:
            task_group = self.data.task_groups[task_group_id]
            self.variants.append(task_group)

        # List of buildings that units can create
        self.creates = []

    def contains_entity(self, unit_id):
        for task_group in self.variants:
            if task_group.contains_entity(unit_id):
                return True

        return False

    def has_command(self, command_id):
        for variant in self.variants:
            for genie_unit in variant.line:
                commands = genie_unit.get_member("unit_commands").get_value()

                for command in commands:
                    type_id = command.get_value()["type"].get_value()

                    if type_id == command_id:
                        return True

        return False

    def is_creatable(self):
        """
        Villagers are creatable if any of their variant task groups are creatable.

        :returns: True if any train location obj_id is greater than zero.
        """
        for variant in self.variants:
            if variant.is_creatable():
                return True

        return False

    def is_garrison(self):
        return False

    def is_gatherer(self):
        return True

    def is_unique(self):
        return False

    def is_projectile_shooter(self):
        # TODO: Only hunting; should be done differently?
        return False

    def get_garrison_mode(self):
        return None

    def get_head_unit_id(self):
        """
        For villagers, this returns the group obj_id.
        """
        return self.get_id()

    def get_head_unit(self):
        """
        For villagers, this returns the group obj_id.
        """
        return self.variants[0].line[0]

    def get_units_with_command(self, command_id):
        """
        Returns all genie units which have the specified command.
        """
        matching_units = []

        for variant in self.variants:
            for genie_unit in variant.line:
                commands = genie_unit.get_member("unit_commands").get_value()

                for command in commands:
                    type_id = command.get_value()["type"].get_value()

                    if type_id == command_id:
                        matching_units.append(genie_unit)

        return matching_units

    def get_train_location_id(self):
        """
        Returns the group_id for building line if the task group is
        creatable, otherwise return None.
        """
        for variant in self.variants:
            if variant.is_creatable():
                return variant.get_train_location_id()

        return None

    def __repr__(self):
        return "GenieVillagerGroup<%s>" % (self.get_id())


class GenieGarrisonMode(Enum):
    """
    Garrison mode of a genie group. This should not be confused with
    the "garrison_type" from the .dat file. These garrison modes reflect
    how the garrison will be handled in the openage API.
    """

    # Keys = all possible creatable types; may be specified further by other factors
    # The negative integers at the start of the tupe prevent Python from creating
    # aliases for the enums.
    NATURAL       = (-1, 1, 2, 3, 5, 6)  # enter/exit/remove; rally point
    UNIT_GARRISON = (-2, 1, 2, 5)        # enter/exit/remove; no cavalry/monks; speedboost for infantry; no rally point
    TRANSPORT     = (-3, 1, 2, 3, 5, 6)  # enter/exit/remove; no rally point
    SELF_PRODUCED = (-4, 1, 2, 3, 5, 6)  # enter only with OwnStorage; exit/remove; only produced units; rally point
    MONK          = (-5, 4,)             # remove/collect/transfer; only relics; no rally point
