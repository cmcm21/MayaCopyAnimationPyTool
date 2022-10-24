import pymel.core as pymel
from enum import Enum
import json


class ConstrainEnum(Enum):
    PARENT_CONSTRAIN = 0
    POINT_CONSTRAIN = 1
    ORIENT_CONSTRAIN = 2
    SCALE_CONSTRAIN = 3


class Constrain(object):

    def __init__(self, constrain: ConstrainEnum):
        self.constrainEnum = constrain
        self.skipX = False
        self.skipY = False
        self.skipZ = False
        self.constraint = None

    def apply(self, source, target):
        if self.constrainEnum == ConstrainEnum.PARENT_CONSTRAIN:
            self.constraint = pymel.parentConstraint(
                source,
                target,
                maintainOffset=True,
                skipRotate=self._get_axes_skip(),
                skipTranslate=self._get_axes_skip()
            )
        elif self.constrainEnum == ConstrainEnum.POINT_CONSTRAIN:
            self.constraint = pymel.pointConstraint(
                source,
                target,
                maintainOffset=True,
                skip=self._get_axes_skip()
            )
        elif self.constrainEnum == ConstrainEnum.ORIENT_CONSTRAIN:
            self.constraint = pymel.orientConstraint(
                source,
                target,
                maintainOffset=True,
                skip=self._get_axes_skip()
            )
        elif self.constrainEnum == ConstrainEnum.SCALE_CONSTRAIN:
            self.constraint = pymel.scaleConstraint(
                source,
                target,
                maintainOffset=True,
                skip=self._get_axes_skip()
            )

    def _get_axes_skip(self):
        skip = "none"
        skip_list = []
        if self.skipX:
            skip_list.append("x")
        if self.skipY:
            skip_list.append("y")
        if self.skipZ:
            skip_list.append("z")

        if len(skip_list) == 1:
            return skip_list[0]
        else:
            return skip if len(skip_list) == 0 else skip_list

    def update_skip_axe(self, axe: str, value: bool):
        if axe == "X":
            self.skipX = value
        elif axe == "Y":
            self.skipY = value
        elif axe == "Z":
            self.skipZ = value

    def get_axes_tuple(self) -> (bool, bool, bool):
        return self.skipX, self.skipY, self.skipZ


class JsonDataManager(object):
    def __init__(self):
        self.data = {}
        self.sourcesKey = "sources"
        self.targetsKey = "targets"
        self.constraintsKey = "constraints"

        return

    def set_data(self, sources: list, targets: list, constraints: list):
        if len(sources) != len(targets) or len(targets) != len(constraints):
            return

        self.data = {
            self.sourcesKey: sources,
            self.targetsKey: targets,
            self.constraintsKey: constraints
        }

    def save(self, file_name):
        if file_name is None:
            return

        with open(file_name, "w") as save_file:
            json.dump(self.data, save_file)

    def load(self, file_name) -> bool:
        if file_name is None:
            return False

        with open(file_name, "r") as load_file:
            data = json.load(load_file)
            if self._check_correct_format(data):
                self.data = data
                return True
            else:
                return False

    def _check_correct_format(self, data: dict) -> bool:
        return self.sourcesKey in data.keys() and \
               self.targetsKey in data.keys() and \
               self.constraintsKey in data.keys()

    def get_data(self, key):
        if key == "t":
            key = self.targetsKey
        elif key == "s":
            key = self.sourcesKey
        elif key == "c":
            key = self.constraintsKey
        else:
            key = ""

        if key in self.data.keys():
            return self.data[key]
        else:
            return []


class ConstrainsMatchingTool(object):

    def __init__(self):
        self._init_class_var()

        if pymel.window(self.window, exists=True):
            pymel.deleteUI(self.window, window=True)

        self.window = pymel.window(self.window, title=self.title, widthHeight=self.windowSize)

        self.mainLayout = pymel.columnLayout(adj=True)
        pymel.text(self.title)
        pymel.separator(height=20)

        self._create_windows_fields()

        pymel.showWindow()

    def _init_class_var(self):
        self.window = "CM_Window"
        self.title = "Constraints creator"
        self.windowSize = (800, 850)
        self.targetUIList = []
        self.sourceXTargetLayouts = []
        self.sourceChildren = []
        self.targetList = []
        self.constraints = []
        self.sourceObjectName = None

    def _create_windows_fields(self):
        self._create_source_section()
        self._create_target_section()

    def _create_source_section(self):
        pymel.text("Source object")
        self.sourceLayout = pymel.rowLayout(
            parent=self.mainLayout,
            columnAlign5=["center"] * 5,
            numberOfColumns=5
        )

        self.sourceTextfield = pymel.textFieldGrp(
            label="Source root",
            parent=self.sourceLayout,
            editable=True
        )

        self._create_source_options()

    def _create_source_options(self):
        self.getSelectedButton = pymel.button(
            label="Get selected",
            parent=self.sourceLayout,
            command=self._get_source_from_selection
        )

        self.getChildrenFromObjectButton = pymel.button(
            label="Get children",
            parent=self.sourceLayout,
            command=self._get_children_from_source
        )

        self.clearButton = pymel.button(
            label="Clear",
            parent=self.sourceLayout,
            command=self._clear_UI
        )

        self.loadJsonButton = pymel.button(
            label="Load Json",
            parent=self.sourceLayout,
            command=self._load_json
        )
        pymel.separator(parent=self.mainLayout)

    def _create_target_section(self):
        self.scrollLayout = pymel.scrollLayout(
            parent=self.mainLayout,
            childResizable=True,
            height=500,
        )
        self.targetUIList.append(pymel.separator(parent=self.mainLayout))
        self.targetUIList.append(pymel.button(
            label="Apply",
            parent=self.mainLayout,
            command=self._apply_constrains
        ))
        self.targetUIList.append(pymel.separator(parent=self.mainLayout))
        self.targetUIList.append(pymel.button(
            label="Delete constraints",
            parent=self.mainLayout,
            command=self._delete_constraints
        ))
        self.targetUIList.append(pymel.separator(parent=self.mainLayout))
        self.targetUIList.append(pymel.button(
            label="Save as json",
            parent=self.mainLayout,
            command=self._save_as_json
        ))
        self.targetUIList.append(pymel.separator(parent=self.mainLayout))

        self.targetUIList.append(self.scrollLayout)

    def _get_source_from_selection(self, *args):
        selected_list = pymel.ls(selection=True)
        if len(selected_list) == 0:
            return

        self.sourceObjectName = selected_list[0]
        pymel.textFieldGrp(self.sourceTextfield, edit=True, text=self.sourceObjectName, editable=False)
        return

    def _get_children_from_source(self, *args):
        if self.sourceObjectName is None:
            return

        self.sourceChildren = pymel.listRelatives(self.sourceObjectName, allDescendents=True)
        self.sourceChildren.append(self.sourceObjectName)
        self.sourceChildren.reverse()

        self.targetList = [""] * len(self.sourceChildren)
        self.constraints = [{} for i in range(len(self.sourceChildren))]

        self._display_matching_source_x_target()
        return

    def _display_matching_source_x_target(self):
        if len(self.sourceChildren) == 0 or len(self.targetList) == 0:
            return

        for i in range(len(self.sourceChildren)):
            self._create_source_x_target_row(i)

    def _create_source_x_target_row(self, index: int):
        separator = pymel.separator(parent=self.scrollLayout)
        container_layout = pymel.rowLayout(
            parent=self.scrollLayout,
            numberOfColumns=2,
            adjustableColumn=2,
            rowAttach=[1, "top", 3]
        )
        self.sourceXTargetLayouts.append(container_layout)
        self.sourceXTargetLayouts.append(separator)

        self._create_source_column(container_layout, index)
        self._create_target_column(container_layout, index)
        return

    def _create_source_column(self, layout, index: int):
        source_name = self.sourceChildren[index].name()
        row_layout = pymel.columnLayout(parent=layout, adjustableColumn=True)

        source_text_field = pymel.textFieldGrp(
            label="Source: ",
            parent=row_layout,
            text=source_name,
            editable=False,
            columnAlign=[1, "center"]
        )

        source_add_target_button = pymel.button(
            label="Add target",
            parent=row_layout,
            command=lambda *args: self._add_extra_target(index)
        )

    def _add_extra_target(self, index: int):
        source = self.sourceChildren[index]
        if self.sourceChildren.count(source) > 1:
            print("Each source can have 2 target at most")
        else:
            index_updated = index + 1
            self.sourceChildren.insert(index_updated, source)
            self.targetList.insert(index_updated, "")
            self.constraints.insert(index_updated, {})
            self._delete_source_x_target_layouts()

            self._display_matching_source_x_target()
        return

    def _delete_source_x_target_layouts(self):
        for layout in self.sourceXTargetLayouts:
            pymel.deleteUI(layout)

        self.sourceXTargetLayouts.clear()

    def _create_target_column(self, layout, index: int):
        self.targetLayout = pymel.columnLayout(parent=layout, adjustableColumn=True)

        target = self.targetList[index]
        target_text_field = pymel.textFieldButtonGrp(
            label="Target :",
            parent=self.targetLayout,
            editable=True,
            text=target,
            buttonLabel="Get selected",
            buttonCommand=lambda *args: self._on_target_select(target_text_field, index)
        )
        target_delete_button = pymel.button(
            label="Delete target",
            parent=self.targetLayout,
            command=lambda *args: self._delete_target(index)
        )
        self._create_constrains_checkbox(self.targetLayout, index)
        return

    def _delete_target(self, index):
        source = self.sourceChildren[index]
        if self.sourceChildren.count(source) > 1:
            self.sourceChildren.pop(index)
            self.targetList.pop(index)
            self.constraints.pop(index)

            self._delete_source_x_target_layouts()
            self._display_matching_source_x_target()
        else:
            print("One target per source is needed at least")
        return

    def _create_constrains_checkbox(self, layout, index):
        constraints_label = pymel.text("Constraints", parent=layout)
        parent_check_box = self._create_constrain_checkbox(layout, index, ConstrainEnum.PARENT_CONSTRAIN, "Parent")
        point_check_box = self._create_constrain_checkbox(layout, index, ConstrainEnum.POINT_CONSTRAIN, "Point")
        orient_check_box = self._create_constrain_checkbox(layout, index, ConstrainEnum.ORIENT_CONSTRAIN, "Orient")
        scale_check_box = self._create_constrain_checkbox(layout, index, ConstrainEnum.SCALE_CONSTRAIN, "Scale")
        return

    def _create_constrain_checkbox(self, layout, index, constrain_enum: ConstrainEnum, label):
        row_layout = pymel.rowLayout(parent=layout, adjustableColumn=1, numberOfColumns=2)
        constrain_value = constrain_enum in self.constraints[index].keys()

        check_box = pymel.checkBox(
            parent=row_layout,
            label=label,
            value=constrain_value,
            onCommand=lambda *args: self._create_constrain_axes(index, constrain_enum),
            offCommand=lambda *args: self._delete_constrain(index, constrain_enum)
        )
        axes = self._get_axes_values(index, constrain_enum)
        axes_checkbox = pymel.checkBoxGrp(
            parent=row_layout,
            numberOfCheckBoxes=3,
            label="Skip axes",
            labelArray3=["x", "y", "z"],
            value1=axes[0], value2=axes[1], value3=axes[2],
            onCommand1=lambda *args: self._update_constrain_axes(index, constrain_enum, "X", True),
            onCommand2=lambda *args: self._update_constrain_axes(index, constrain_enum, "Y", True),
            onCommand3=lambda *args: self._update_constrain_axes(index, constrain_enum, "Z", True),
            offCommand1=lambda *args: self._update_constrain_axes(index, constrain_enum, "X", False),
            offCommand2=lambda *args: self._update_constrain_axes(index, constrain_enum, "Y", False),
            offCommand3=lambda *args: self._update_constrain_axes(index, constrain_enum, "Z", False)
        )
        return check_box

    def _get_axes_values(self, index, constrain_enum) -> (bool, bool, bool):
        if constrain_enum in self.constraints[index]:
            constraint: Constrain = self.constraints[index][constrain_enum]
            return constraint.get_axes_tuple()
        else:
            return False, False, False

    def _delete_constrain(self, index, constrain_enum):
        if constrain_enum in self.constraints[index]:
            self.constraints[index].pop(constrain_enum)
        return

    def _create_constrain_axes(self, index, constrain_enum: ConstrainEnum):
        self.constraints[index][constrain_enum] = Constrain(constrain_enum)
        return

    def _update_constrain_axes(self, index: int, constrain_enum: ConstrainEnum, skip_axe: str, value: bool):
        if constrain_enum in self.constraints[index].keys():
            self.constraints[index][constrain_enum].update_skip_axe(skip_axe, value)

    def _on_target_select(self, text_field, index: int):
        selected_list = pymel.ls(selection=True)
        if len(selected_list) == 0:
            return

        target = selected_list[0]
        pymel.textFieldGrp(text_field, edit=True, text=target)
        self.targetList[index] = target.name()
        return

    def _apply_constrains(self, *args):
        for i in range(len(self.sourceChildren)):
            if self.targetList[i] == "":
                continue

            source = self.sourceChildren[i]
            target = self.targetList[i]
            for constrain in self.constraints[i].values():
                constrain.apply(source, target)

        self._clear_UI()

    def _clear_UI(self, *args):
        for ui in self.targetUIList:
            pymel.deleteUI(ui)

        self.targetUIList.clear()
        self.sourceChildren.clear()
        self.targetList.clear()
        self.constraints.clear()
        self.sourceXTargetLayouts.clear()

        self._create_target_section()
        return

    def _delete_constraints(self,*args):
        if not self._validate_self_data():
            return

        for i in range(len(self.constraints)):
            constraint:Constrain = self.constraints[i]
            pymel.delete(constraint.constraint)
        print("++++ constraints deleted ++++")

    def _save_as_json(self,*args):
        if not self._validate_self_data():
            print("There is no constraints configuration to save")
            return

        save_file = pymel.fileDialog2(
            fileFilter="*.json",
            dialogStyle=2
        )

        data = JsonDataManager()
        data.set_data(self.sourceChildren,self.targetList,self.constraints)
        data.save(save_file)

    def _load_json(self, *args):
        load_file = pymel.fileDialog2(
            fileFilter="*.json",
            fileMode=1,
            dialogStyle=2
        )
        data = JsonDataManager()
        if data.load(load_file):
            self.targetList = data.get_data("t")
            self.constraints = data.get_data("c")
            self.sourceChildren = data.get_data("s")
            if self._validate_self_data():
                self._display_matching_source_x_target()
            else:
                print("++++++++ json format error ++++++++")
        else:
            print("++++ error trying to read json occurred ++++")
        return

    def _validate_self_data(self):
        return len(self.targetList) > 0 and len(self.constraints) > 0 and len(self.sourceChildren) > 0


def main():
    constrains_tool = ConstrainsMatchingTool()


if __name__ == "__main__":
    main()
