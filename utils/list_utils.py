def remove_duplicates_preserve_order(seq):
    """
    리스트에서 중복 값을 제거하면서 원래 순서를 유지합니다.

    :param seq: 입력 리스트
    :return: 중복 값이 제거된 리스트
    """
    seen = set()
    result = []
    for item in seq:
        if item[0] not in seen:
            seen.add(item[0])
            result.append(item)
    return result