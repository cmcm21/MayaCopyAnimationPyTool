import pymel.core as pymel
from enum import Enum


class ConstrainEnum(Enum):
    PARENT_CONSTRAIN = 0
    POINT_CONSTRAIN = 1
    ORIENT_CONSTRAIN = 2
    SCALE_CONSTRAIN = 3


class Constrain(object):

    def __init__(self, constrain: ConstrainEnum):
        self.constrain = constrain
        self.skipX = False
        self.skipY = False
        self.skipZ = False

    def apply(self, source, target):
        if self.constrain == ConstrainEnum.PARENT_CONSTRAIN:
            pymel.parentConstraint(
                source,
                target,
                skipRotate=self._get_axes_skip(),
                skipTranslate=self._get_axes_skip()
            )
        elif self.constrain == ConstrainEnum.POINT_CONSTRAIN:
            pymel.pointConstraint(
                source,
                target,
                skip=self._get_axes_skip()
            )
        elif self.constrain == ConstrainEnum.ORIENT_CONSTRAIN:
            pymel.orientConstraint(
                source,
                target,
                skip=self._get_axes_skip()
            )
        elif self.constrain == ConstrainEnum.SCALE_CONSTRAIN:
            pymel.scaleConstraint(
                source,
                target,
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

    def update_skip_axe(self,axe:str,value:bool):
        if axe == "X":
            self.skipX = value
        elif axe == "Y":
            self.skipY = value
        elif axe == "Z":
            self.skipZ = value


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
        self.windowSize = (900, 800)
        self.targetUIList = []

    def _create_windows_fields(self):
        self._create_source_section()
        self._create_target_section()

    def _create_source_section(self):
        pymel.text("Source object")
        self.sourceLayout = pymel.rowLayout(
            parent=self.mainLayout,
            columnAlign=[1,"center"],
            numberOfColumns=4
        )

        self.sourceTextfield = pymel.textFieldGrp(
            label="Source root",
            parent=self.sourceLayout,
            editable=True
        )

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

    def _create_target_section(self):
        self.scrollLayout = pymel.scrollLayout(
            parent=self.mainLayout,
            childResizable=True,
            height=725,
        )

        self.applyAnimationButton = pymel.button(
            label="Apply",
            parent=self.mainLayout,
            command=self._apply_constrains
        )

        self.targetUIList.append(self.scrollLayout)
        self.targetUIList.append(self.applyAnimationButton)

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
        self.constrains = [{} for i in range(len(self.sourceChildren))]

        self._display_matching_source_x_target()
        return

    def _display_matching_source_x_target(self):
        if len(self.sourceChildren) == 0 or len(self.targetList) == 0:
            return

        for i in range(len(self.sourceChildren)):
            self._create_source_x_target_row(i)

    def _create_source_x_target_row(self, index: int):
        container_layout = pymel.rowLayout(
            parent=self.scrollLayout,
            numberOfColumns=2,
            rowAttach=[1,"top",0]
        )
        self._create_source_column(container_layout,index)
        self._create_target_column(container_layout,index)
        return

    def _create_source_column(self,layout,index:int):
        source_name = self.sourceChildren[index].name()

        source_text_field = pymel.textFieldGrp(
            label="Source: ",
            parent=layout,
            text=source_name,
            editable=False,
            columnAlign=[1,"center"]
        )

    def _create_target_column(self,layout,index:int):
        target_layout = pymel.columnLayout(parent=layout, adjustableColumn=True)

        target_text_field = pymel.textFieldButtonGrp(
            label="Target :",
            parent=target_layout,
            editable=True,
            buttonLabel="Get selected",
            buttonCommand=lambda *args: self._on_target_select(
                target_text_field, index)
        )

        self._create_constrains_checkbox(target_layout,index)
        return

    def _create_constrains_checkbox(self, layout,index):
        constraints_label = pymel.text("Constraints",parent=layout)
        parent_check_box = self._create_constrain_checkbox(layout,index,ConstrainEnum.PARENT_CONSTRAIN,"Parent")
        point_check_box = self._create_constrain_checkbox(layout,index,ConstrainEnum.POINT_CONSTRAIN,"Point")
        orient_check_box = self._create_constrain_checkbox(layout,index,ConstrainEnum.ORIENT_CONSTRAIN,"Orient")
        scale_check_box = self._create_constrain_checkbox(layout,index,ConstrainEnum.SCALE_CONSTRAIN,"Scale")

        return

    def _create_constrain_checkbox(self,layout,index,constrain_enum:ConstrainEnum,label):
        row_layout = pymel.rowLayout(parent=layout,adjustableColumn=1,numberOfColumns=2)

        check_box = pymel.checkBox(
            parent=row_layout,
            label=label,
            onCommand=lambda *args: self._create_constrain_axes(index,constrain_enum),
            offCommand=lambda *args: self._delete_constrain(index,constrain_enum)
        )

        axes_checkbox = pymel.checkBoxGrp(
            parent=row_layout,
            numberOfCheckBoxes=3,
            label="Skip axes",
            labelArray3=["x","y","z"],
            onCommand1=lambda *args: self._update_constrain_axes(index,constrain_enum,"X",True),
            onCommand2=lambda *args: self._update_constrain_axes(index,constrain_enum,"Y", True),
            onCommand3=lambda *args: self._update_constrain_axes(index,constrain_enum,"Z", True),
            offCommand1=lambda *args: self._update_constrain_axes(index,constrain_enum,"X",False),
            offCommand2=lambda *args: self._update_constrain_axes(index,constrain_enum,"Y", False),
            offCommand3=lambda *args: self._update_constrain_axes(index,constrain_enum,"Z", False)
        )
        return check_box

    def _delete_constrain(self,index,constrain_enum):
        if constrain_enum in self.constrains[index]:
            self.constrains[index].pop(constrain_enum)
        return

    def _create_constrain_axes(self, index, constrain_enum:ConstrainEnum):
        self.constrains[index][constrain_enum] = Constrain(constrain_enum)
        return

    def _update_constrain_axes(self,index:int,constrain_enum:ConstrainEnum,skip_axe:str,value:bool):
        if constrain_enum in self.constrains[index].keys():
            self.constrains[index][constrain_enum].update_skip_axe(skip_axe,value)

    def _on_target_select(self, text_field, index: int):
        selected_list = pymel.ls(selection=True)
        if len(selected_list) == 0:
            return

        target = selected_list[0]
        pymel.textFieldGrp(text_field, edit=True, text=target)
        self.targetList[index] = target.name()
        return

    def _apply_constrains(self,*args):
        for i in range(len(self.sourceChildren)):
            if self.targetList[i] == "":
                continue

            source = self.sourceChildren[i]
            target = self.targetList[i]
            for constrain in self.constrains[i].values():
                constrain.apply(source,target)

        self._clear_UI()

    def _clear_UI(self,*args):
        for ui in self.targetUIList:
            pymel.deleteUI(ui)

        self.targetUIList.clear()
        self.sourceChildren.clear()
        self.targetList.clear()
        self.constrains.clear()

        self._create_target_section()
        return


def main():
    constrains_tool = ConstrainsMatchingTool()


if __name__ == "__main__":
    main()
