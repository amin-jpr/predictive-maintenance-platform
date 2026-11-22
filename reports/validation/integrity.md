# C-MAPSS integrity report — FD001

Generated: 2026-11-07T06:40:03+00:00
Status: **PASS**

## Checks

| Check | Result | Severity | Details |
|---|---|---|---|
| required_files_exist | PASS | error | {'missing': []} |
| train_columns | PASS | error | {'columns': ['engine_id', 'cycle', 'setting_1', 'setting_2', 'setting_3', 's_1', 's_2', 's_3', 's_4', 's_5', 's_6', 's_7', 's_8', 's_9', 's_10', 's_11', 's_12', 's_13', 's_14', 's_15', 's_16', 's_17', 's_18', 's_19', 's_20', 's_21']} |
| train_dtypes | PASS | error | {'engine_id': 'int64', 'cycle': 'int64', 'setting_1': 'float64', 'setting_2': 'float64', 'setting_3': 'float64', 's_1': 'float64', 's_2': 'float64', 's_3': 'float64', 's_4': 'float64', 's_5': 'float64', 's_6': 'float64', 's_7': 'float64', 's_8': 'float64', 's_9': 'float64', 's_10': 'float64', 's_11': 'float64', 's_12': 'float64', 's_13': 'float64', 's_14': 'float64', 's_15': 'float64', 's_16': 'float64', 's_17': 'float64', 's_18': 'float64', 's_19': 'float64', 's_20': 'float64', 's_21': 'float64'} |
| train_finite | PASS | error | {} |
| train_engine_count | PASS | error | {'actual': 100, 'expected': 100} |
| train_row_count | PASS | error | {'actual': 20631, 'expected': 20631} |
| train_duplicate_keys | PASS | error | {'duplicate_keys': 0} |
| train_duplicate_rows | PASS | error | {'duplicate_rows': 0} |
| train_cycle_ordering | PASS | error | {'errors': [], 'error_count': 0} |
| train_positive_lengths | PASS | error | {} |
| test_columns | PASS | error | {'columns': ['engine_id', 'cycle', 'setting_1', 'setting_2', 'setting_3', 's_1', 's_2', 's_3', 's_4', 's_5', 's_6', 's_7', 's_8', 's_9', 's_10', 's_11', 's_12', 's_13', 's_14', 's_15', 's_16', 's_17', 's_18', 's_19', 's_20', 's_21']} |
| test_dtypes | PASS | error | {'engine_id': 'int64', 'cycle': 'int64', 'setting_1': 'float64', 'setting_2': 'float64', 'setting_3': 'float64', 's_1': 'float64', 's_2': 'float64', 's_3': 'float64', 's_4': 'float64', 's_5': 'float64', 's_6': 'float64', 's_7': 'float64', 's_8': 'float64', 's_9': 'float64', 's_10': 'float64', 's_11': 'float64', 's_12': 'float64', 's_13': 'float64', 's_14': 'float64', 's_15': 'float64', 's_16': 'float64', 's_17': 'float64', 's_18': 'float64', 's_19': 'float64', 's_20': 'float64', 's_21': 'float64'} |
| test_finite | PASS | error | {} |
| test_engine_count | PASS | error | {'actual': 100, 'expected': 100} |
| test_row_count | PASS | error | {'actual': 13096, 'expected': 13096} |
| test_duplicate_keys | PASS | error | {'duplicate_keys': 0} |
| test_duplicate_rows | PASS | error | {'duplicate_rows': 0} |
| test_cycle_ordering | PASS | error | {'errors': [], 'error_count': 0} |
| test_positive_lengths | PASS | error | {} |
| rul_length | PASS | error | {'rul_values': 100, 'test_engines': 100} |
| rul_nonnegative_integer | PASS | error | {'min': 7, 'max': 145} |
| rul_alignment_convention | PASS | error | {'note': 'RUL file has no engine IDs; aligned to sorted test engine IDs per NASA convention', 'test_ids_sorted_contiguous': True} |
| train_test_numeric_id_overlap_allowed | PASS | info | {'note': 'Train/test engine IDs are separate namespaces; numeric overlap is expected', 'overlap_count': 100} |
| sha256_train_FD001.txt | PASS | error | {'expected': '963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8', 'actual': '963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8'} |
| sha256_test_FD001.txt | PASS | error | {'expected': '3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851', 'actual': '3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851'} |
| sha256_RUL_FD001.txt | PASS | error | {'expected': 'a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca', 'actual': 'a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca'} |

## Summary

Train: {'engines': 100, 'observations': 20631, 'min_cycle': 1, 'max_cycle': 362, 'min_sequence_length': 128, 'max_sequence_length': 362, 'mean_sequence_length': 206.31}
Test: {'engines': 100, 'observations': 13096, 'min_cycle': 1, 'max_cycle': 303, 'min_sequence_length': 31, 'max_sequence_length': 303, 'mean_sequence_length': 130.96}
RUL: {'count': 100, 'min': 7, 'max': 145, 'mean': 75.52, 'terminal_test_rul_aligned_to_sorted_engine_ids': True}
Constant sensors: ['s_1', 's_5', 's_10', 's_16', 's_18', 's_19']
Near-constant sensors: ['s_6', 's_8', 's_13']
