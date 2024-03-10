from ui_generator import UiGenerator
from ui_callbacks import UiCallbacks
from feedback_processor import FeedbackProcessor
from hw_control_process import hw_process
from config_handler import ConfigHandler
import data_structures as ds
from nicegui import ui
import multiprocessing as mp


if __name__ == "__main__":
    q_command = mp.Queue(maxsize=10)
    q_feedback = mp.Queue(maxsize=10)

    ui_objects = ds.UiObjects()
    conf_h = ConfigHandler(ui_objects)
    conf_h.load_config()

    ui_cb = UiCallbacks(ui_objects, q_command)
    ui_gen = UiGenerator(ui_objects, ui_cb)
    fp = FeedbackProcessor(q_feedback, ui_objects)

    ui_gen.create_ui()

    #mp.set_start_method('fork')
    p = mp.Process(target=hw_process, args=(q_command, q_feedback))
    p.start()
    ui_cb.init_devices()

    ui.timer(2, ui_cb.request_vna_data)
    ui.timer(0.01, fp.check_queue)
    
    ui.run( port=8050, reload=False)
    q_command.put({'op':'terminate'})
    p.join()