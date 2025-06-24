from typing import Literal
import streamlit as st

from ..driver import Driver


class App:
    def __init__(self) -> None:
        self.setup()

    @staticmethod
    def display_task(key: str, task: dict, priority: Literal["L", "H"]) -> None:
        driver: Driver = st.session_state.driver
        color = "blue"
        status_label = ""
        status_icon = ""
        badge_color = "blue"
        badge_label = "LOW⠀ PRIORITY"
        badge_icon = ":material/priority_high:"
        if priority == "H":
            color = "violet"
            badge_color = "violet"
            badge_label = "HIGH PRIORITY"
            badge_icon = ":material/star:"
        if task["is_complete"]:
            color = "green"
            status_label = "COMPLETED"
            status_icon = ":material/done_all:"
        if task["is_expired"]:
            color = "grey"
            status_label = "⠀EXPIRED⠀"
            status_icon = ":material/skull:"
        st.subheader(task["name"], anchor=False, divider=color)
        col1, col2, col3 = st.columns([1, 2.8, 1.2], gap="small", vertical_alignment="center")
        col1.badge(label=badge_label, color=badge_color, icon=badge_icon)
        if task["is_complete"] or task["is_expired"]:
            col2.badge(label=status_label, color=color, icon=status_icon)
        if task["expires_at"]:
            exp = "Expires by "
            if task["is_expired"]:
                exp = "Expired on "
            col3.write(f"{exp}{task['expires_at']}")
        if task["details"] and not str.isspace(task["details"]):
            st.write(task["details"])
        col1, col2 = st.columns([1.4, 0.17], gap="large", vertical_alignment="center")
        if col1.button(":material/done_outline:", key=f"complete_{key}", disabled=task["is_complete"] or task["is_expired"], help="Mark this task as Complete"):
            driver.complete_task(task["name"], priority)
            st.rerun()
        if col2.button(":material/delete:", key=f"delete_{key}", help="Delete this task"):
            driver.remove_task(task["name"], priority)
            st.rerun()

    def setup(self) -> None:
        if "loaded" not in st.session_state:
            st.session_state["loaded"] = True
            st.session_state["driver"] = Driver(priority_maxsize=2)
            st.session_state["creation"] = False

    @st.dialog("Enter Task Details")
    def add_task_dialog(self) -> None:
        driver: Driver = st.session_state.driver
        with st.container(key="addtask_form", border=True):
            task_title = st.text_input(label=" ", placeholder="Title for the task...", label_visibility="collapsed", max_chars=75)
            task_desc = st.text_input(label=" ", placeholder="Task details (optional)...", label_visibility="collapsed")
            high_priority = st.toggle("High Priority", disabled=len(driver.high_priority_tasks) == driver.priority_maxsize)
            expiry_date = None
            if st.toggle("Set Expiry"):
                expiry_date = st.date_input(label="Date")
            if st.button("Confirm Details", key="formbutton"):
                driver.add_task(task_title, task_desc, "H" if high_priority else "L", expire=expiry_date)
                st.rerun()

    def dashboard_page(self) -> None:
        driver: Driver = st.session_state.driver
        driver.check_expiry()
        st.title("Task List", anchor=False)
        if st.button("Add Task", key="button_addtask", disabled=driver.is_full):
            self.add_task_dialog()
        for task in driver.high_priority_tasks:
            with st.container(key=f"container_{task}", border=True):
                self.display_task(task, driver.high_priority_tasks[task], "H")
        for task in driver.low_priority_tasks:
            with st.container(key=f"container_{task}", border=True):
                self.display_task(task, driver.low_priority_tasks[task], "L")


    def run(self) -> None:
        self.dashboard_page()