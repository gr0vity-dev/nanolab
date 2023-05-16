from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from nanolab.loggers.contracts import ISink, LogData
from nanolab.decorators import print_dot
from os import environ

Base = declarative_base()


class SqlLog(Base):
    __tablename__ = "nanolab_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(Integer, ForeignKey('nanolab_testcases.id'))
    timestamp = Column(String)
    elapsed_time = Column(Integer)
    check_count = Column(Integer)
    cemented_count = Column(Integer)
    percent_cemented = Column(Float)
    percent_checked = Column(Float)
    cps_avg = Column(Float)


class SqlTestCase(Base):
    __tablename__ = "nanolab_testcases"

    id = Column(Integer, primary_key=True)
    testcase_name = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    status = Column(String)

    logs = relationship("SqlLog", backref="testcase")


class SqlSink(ISink):

    def __init__(self, **kwargs):
        self.db_uri = kwargs['db_uri']
        self.milestones = kwargs['milestones']
        self.testcase_name = kwargs.get(
            'testcase_name', environ.get("LAB_TESTCASE", "UNDEFINED"))
        self.start_date = None
        self.end_date = None
        self.status = 'Running'

        self.engine = create_engine(self.db_uri)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        self.testcase_id = self.store_testcase()

    def store_testcase(self):
        session = self.Session()
        new_testcase = SqlTestCase(testcase_name=self.testcase_name,
                                   start_date=self.start_date,
                                   end_date=self.end_date,
                                   status=self.status)
        session.add(new_testcase)
        session.commit()
        testcase_id = new_testcase.id
        session.close()
        return testcase_id

    def update_testcase(self, status):
        session = self.Session()
        testcase = session.query(SqlTestCase).filter_by(
            id=self.testcase_id).first()
        testcase.end_date = self.end_date
        testcase.status = status
        session.commit()
        session.close()

    @print_dot
    def store_logs(self, logs: LogData):
        if self.milestones and logs.percent_cemented >= min(self.milestones):
            session = self.Session()
            new_log = SqlLog(testcase_id=self.testcase_id,
                             timestamp=logs.timestamp,
                             elapsed_time=logs.elapsed_time,
                             check_count=logs.check_count,
                             cemented_count=logs.cemented_count,
                             percent_cemented=logs.percent_cemented,
                             percent_checked=logs.percent_checked,
                             cps_avg=logs.cps_avg)
            session.add(new_log)
            session.commit()
            session.close()
            self.milestones = {
                milestone
                for milestone in self.milestones
                if milestone > logs.percent_cemented
            }
            if logs.percent_cemented == 100:
                self.status = "PASS"

    def end(self):
        status = "FAIL" if self.status == "RUNNING" else self.status
        self.update_testcase(status)

    def get_testcase(self, id):
        with self.Session() as session:
            return session.query(SqlTestCase).filter_by(id=id).first()

    def get_log(self, testcase_id):
        with self.Session() as session:
            return session.query(SqlLog).filter_by(
                testcase_id=testcase_id).first()
