from app.models import *
from app import db
from app.parser import *
from datetime import datetime
from pytz import timezone
from app.commons import *
import time, json

class TaskUtil(object):

    @staticmethod
    def get_task_name(session, result_id):
        return '{}@{}#{}'.format(session.name, session.algorithm, result_id)

    @staticmethod
    def save_execution_time(module, start_ts, fn, result_id=None):
        end_ts = time.time()
        exec_time = end_ts - start_ts
        start_time = datetime.fromtimestamp(int(start_ts), timezone(TIME_ZONE))
        db.session.add(ExecutionTime(module=module, function=fn, tag="",
                                     start_time=start_time, execution_time=exec_time, result_id=result_id))
        return exec_time

    @staticmethod
    def create_and_save_recommendation(recommended_knobs, result, status, **kwargs):
        session = Session.query.filter(Session.id == result.session_id).first()
        system_id = session.system_id
        parser = FormatParser(system_id)
        formatted_knobs = parser.format_system_knobs(recommended_knobs)
        config = parser.create_knob_configuration(formatted_knobs)
        retval = dict(**kwargs)
        retval.update(
            status=status,
            result_id=result.id,
            recommendation=config
        )
        result.next_configuration = json.dumps(retval)
        db.session.commit()

        return retval

    @staticmethod
    def check_early_return(data):
        newest_result = Result.query.filter(Result.id == data['newest_result_id']).first()
        if data.get('status', 'good') != 'good':  # No status or status is not 'good'
            if data['status'] == 'lhs':
                info = 'The config is generated by LHS.'
            else:
                info = 'Unknown.'
            info += ' ' + data.get('debug', '')
            target_data_res = TaskUtil.create_and_save_recommendation(
                recommended_knobs=data['config_recommend'], result=newest_result,
                status=data['status'], info=info, pipeline_run=None)
            return True, target_data_res
        return False, None