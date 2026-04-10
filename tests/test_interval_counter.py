"""
اختبارات عداد الفترات الزمنية - Interval Counter Tests
======================================================
"""

import time
import pytest
from engine.interval_counter import IntervalCounter, IntervalRecord


class TestIntervalCounterInit:
    def test_default_interval_none(self):
        counter = IntervalCounter()
        assert counter.get_interval() == IntervalCounter.INTERVAL_NONE

    def test_default_not_active(self):
        counter = IntervalCounter()
        assert not counter.is_active

    def test_default_history_empty(self):
        counter = IntervalCounter()
        assert counter.get_history() == []


class TestIntervalCounterSetInterval:
    def test_set_interval_5_min(self):
        counter = IntervalCounter()
        counter.set_interval(300)
        assert counter.get_interval() == 300

    def test_set_interval_zero(self):
        counter = IntervalCounter()
        counter.set_interval(0)
        assert counter.get_interval() == 0

    def test_set_interval_negative_clamps_to_zero(self):
        counter = IntervalCounter()
        counter.set_interval(-10)
        assert counter.get_interval() == 0


class TestIntervalCounterStartStop:
    def test_start_sets_active(self):
        counter = IntervalCounter()
        counter.start()
        assert counter.is_active

    def test_stop_clears_active(self):
        counter = IntervalCounter()
        counter.start()
        counter.stop()
        assert not counter.is_active

    def test_elapsed_after_start(self):
        counter = IntervalCounter()
        counter.start()
        time.sleep(0.1)
        elapsed = counter.get_elapsed()
        assert elapsed >= 0.1

    def test_elapsed_zero_before_start(self):
        counter = IntervalCounter()
        assert counter.get_elapsed() == 0.0

    def test_total_elapsed_after_start(self):
        counter = IntervalCounter()
        counter.start()
        time.sleep(0.1)
        total = counter.get_total_elapsed()
        assert total >= 0.1


class TestIntervalCounterCheckInterval:
    def test_no_interval_returns_none(self):
        counter = IntervalCounter()
        counter.start()
        result = counter.check_interval({'total': 10})
        assert result is None

    def test_interval_not_elapsed_returns_none(self):
        counter = IntervalCounter()
        counter.set_interval(300)
        counter.start()
        result = counter.check_interval({'total': 5})
        assert result is None

    def test_interval_elapsed_returns_record(self):
        counter = IntervalCounter()
        counter.set_interval(1)
        counter.start()
        time.sleep(1.1)
        record = counter.check_interval({'total': 10, 'in_count': 6, 'out_count': 4})
        assert record is not None
        assert isinstance(record, IntervalRecord)
        assert record.index == 0
        assert record.stats['total'] == 10

    def test_interval_computes_delta(self):
        counter = IntervalCounter()
        counter.set_interval(1)
        counter.start()
        time.sleep(1.1)
        record1 = counter.check_interval({'total': 10, 'in_count': 6, 'out_count': 4})
        assert record1.stats['total'] == 10
        time.sleep(1.1)
        record2 = counter.check_interval({'total': 25, 'in_count': 15, 'out_count': 10})
        assert record2.stats['total'] == 25
        assert record2.stats['in_count'] == 15
        assert record2.stats['out_count'] == 10
        assert record2.index == 1

    def test_multiple_intervals(self):
        counter = IntervalCounter()
        counter.set_interval(1)
        counter.start()
        for i in range(3):
            time.sleep(1.1)
            counter.check_interval({'total': (i + 1) * 10})
        assert len(counter.get_history()) == 3

    def test_interval_after_count_reset(self):
        """
        يحاكي السيناريو الحقيقي:
        الفترة 1: 10 مركبات → إعادة تعيين → الفترة 2: 8 مركبات
        كل فترة تعطي العدد الصحيح المستقل
        """
        counter = IntervalCounter()
        counter.set_interval(1)
        counter.start()
        time.sleep(1.1)
        record1 = counter.check_interval({'total': 10, 'in_count': 6, 'out_count': 4})
        assert record1.stats['total'] == 10
        time.sleep(1.1)
        record2 = counter.check_interval({'total': 8, 'in_count': 5, 'out_count': 3})
        assert record2.stats['total'] == 8
        assert record2.stats['in_count'] == 5
        assert record2.stats['out_count'] == 3


class TestIntervalCounterProgress:
    def test_progress_zero_before_start(self):
        counter = IntervalCounter()
        assert counter.get_progress() == 0.0

    def test_progress_zero_for_full_interval(self):
        counter = IntervalCounter()
        counter.start()
        assert counter.get_progress() == 0.0

    def test_progress_increases(self):
        counter = IntervalCounter()
        counter.set_interval(5)
        counter.start()
        time.sleep(0.5)
        progress = counter.get_progress()
        assert 0 < progress < 1.0


class TestIntervalCounterReset:
    def test_reset_clears_history(self):
        counter = IntervalCounter()
        counter.set_interval(1)
        counter.start()
        time.sleep(1.1)
        counter.check_interval({'total': 10})
        counter.reset()
        assert counter.get_history() == []

    def test_reset_resets_index(self):
        counter = IntervalCounter()
        counter.set_interval(1)
        counter.start()
        time.sleep(1.1)
        counter.check_interval({'total': 10})
        counter.reset()
        assert counter.get_current_interval_number() == 1


class TestIntervalCounterFormatSeconds:
    def test_format_zero(self):
        assert IntervalCounter.format_seconds(0) == "00:00"

    def test_format_seconds_only(self):
        assert IntervalCounter.format_seconds(45) == "00:45"

    def test_format_minutes_seconds(self):
        assert IntervalCounter.format_seconds(125) == "02:05"

    def test_format_hours(self):
        assert IntervalCounter.format_seconds(3661) == "01:01:01"


class TestIntervalCounterPresets:
    def test_presets_exist(self):
        assert len(IntervalCounter.PRESETS) >= 6

    def test_preset_values(self):
        values = [p[0] for p in IntervalCounter.PRESETS]
        assert 0 in values
        assert 300 in values
        assert 900 in values
