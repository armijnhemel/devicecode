#!/usr/bin/env python3

# Licensed under the terms of the Apache license
# SPDX-License-Identifier: Apache-2.0

from typing import Iterable

from textual.suggester import Suggester


class SuggestDevices(Suggester):
    '''A custom suggester, based on the SuggestFromList example from Textual'''

    def __init__(
        self, suggestions: Iterable[str], data, case_sensitive: bool = True) -> None:
        super().__init__(case_sensitive=case_sensitive)
        self._suggestions = list(map(lambda x: x['name'], suggestions))
        self._for_comparison = (
            self._suggestions
            if self.case_sensitive
            else [suggestion.casefold() for suggestion in self._suggestions]
        )

        # mapping of filter name to kwargs names
        # The 'kwargs' are used below to populate the suggestion table
        suggestion_names = {'bootloader': 'bootloaders', 'brand': 'brands',
            'ignore_brand': 'brands', 'chip': 'chips', 'chip_type': 'chip_types',
            'chip_vendor': 'chip_vendors', 'connector': 'connectors', 'cveid': 'cveids',
            'fccid': 'fcc_ids', 'file': 'files', 'flag': 'flags', 'ip': 'ips', 'odm': 'odms',
            'ignore_odm': 'odms', 'package': 'packages', 'partition': 'partitions',
            'password': 'passwords', 'program': 'programs', 'rootfs': 'rootfs', 'sdk': 'sdks',
            'type': 'types'}

        self.suggestion_table = {}
        for name, suggestion in suggestion_names.items():
            self.suggestion_table[name] = sorted(data.get(suggestion, []))

        # some values are always hardcoded
        self.suggestion_table['cpe'] = ['no', 'yes']
        self.suggestion_table['cve'] = ['no', 'yes']
        self.suggestion_table['fcc'] = ['no', 'yes']
        self.suggestion_table['jtag'] = ['no', 'unknown', 'yes']
        self.suggestion_table['serial'] = ['no', 'unknown', 'yes']
        self.suggestion_table['origin'] = ['techinfodepot', 'wikidevi', 'openwrt']
        self.suggestion_table['ignore_origin'] = ['techinfodepot', 'wikidevi', 'openwrt']
        self.suggestion_table['overlays'] = ['off']

    async def get_suggestion(self, value: str) -> str | None:
        """Gets a completion from the given possibilities.

        Args:
            value: The current value.

        Returns:
            A valid completion suggestion or `None`.
        """

        # First split the value. Assume that the suggestions are only
        # for the right most part of the filtering data: if data is changed
        # while there are characters following this data no suggestions will
        # be given for the changed parts.
        check_value = value.rsplit(' ', maxsplit=1)[-1]
        if '=' in check_value:
            name_params, token_value = check_value.split('=', maxsplit=1)

            # When adding a new value the right offset for the
            # string needs to be computed, otherwise some characters
            # will appear to have been overwritten or "hidden".
            len_name_params = len(name_params) + 1
            suggestion_offset = len(check_value)-len_name_params
            name = name_params.split('?', maxsplit=1)[0]

            # Then check and suggest a value. Don't ask how it works,
            # but it works!
            if name in self.suggestion_table:
                for idx, chk in enumerate(self.suggestion_table[name]):
                    if chk.startswith(token_value):
                        return value + self.suggestion_table[name][idx][suggestion_offset:]

        # Suggestions for the token names (without a value)
        for idx, suggestion in enumerate(self._for_comparison):
            if suggestion.startswith(check_value):
                return value + self._suggestions[idx][len(check_value):]
        return None
