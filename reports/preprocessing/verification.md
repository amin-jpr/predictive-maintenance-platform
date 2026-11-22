# Artifact verification — FD001

Status: **PASS**

- artifact_checksums: PASS — {'artifacts': 227, 'failed': []}
- split_isolation: PASS — {'fit': 80, 'validation': 20}
- train_labels_independent: PASS — {'rows': 20631}
- test_labels_independent: PASS — {'rows': 13096}
- scaler_fit_boundary: PASS — {'fit_split': 'train_fit', 'n_fit_engines': 80}
- window_boundaries: PASS — {'windows': 27927}
- window_targets_match_ending_cycle: PASS — {'windows': 27927}
- window_array_dimensions: PASS — {'train_fit': {'file': 'engine_0001.npz', 'X_shape': [163, 30, 92]}, 'validation': {'file': 'engine_0003.npz', 'X_shape': [150, 30, 92]}, 'test': {'file': 'engine_0001.npz', 'X_shape': [2, 30, 92]}}
