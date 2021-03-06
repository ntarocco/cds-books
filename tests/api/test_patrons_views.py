# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# CDS Books is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

from __future__ import absolute_import, print_function

import pytest
from flask import url_for
from invenio_access.models import ActionUsers
from invenio_accounts.models import User
from invenio_accounts.testutils import login_user_via_session
from invenio_app_ils.patrons.indexer import PatronIndexer
from invenio_db import db
from invenio_oauthclient.models import RemoteAccount, UserIdentity
from invenio_search import current_search
from invenio_userprofiles.models import UserProfile

from cds_books.patrons.api import Patron
from cds_books.patrons.permissions import retrieve_patron_loans_access_action


def test_patron_loans_view(app, system_user, testdata, client):
    """Test check for users update in sync command."""

    db.session.add(
        ActionUsers.allow(
            retrieve_patron_loans_access_action, user=system_user)
    )
    db.session.commit()

    patron = Patron(system_user.id)
    PatronIndexer().index(patron)
    current_search.flush_and_refresh(index='*')

    login_user_via_session(client, email=system_user.email)

    resp = client.get(
        url_for(
            "cds_books_patron_loans.patron_loans",
            person_id=1))

    assert resp.status_code == 200

    expected_books_on_loan = [{
        "barcode": "123456789-3",
        "end_date": "2018-07-28",
        "library": "Main Library",
        "location": "Route de Meyrin",
        "title": "Prairie Fires: The American Dreams of Laura Ingalls Wilder"
    }]
    expected_loan_requests = [{
        "request_start_date": "2018-06-28",
        "request_end_date": "2018-07-28",
        "library": "Main Library",
        "location": "Route de Meyrin",
        "title": "The Gulf: The Making of An American Sea"
    }]
    data = resp.json
    assert data["books_on_loan"] == expected_books_on_loan
    assert data["loan_requests"] == expected_loan_requests

    if patron.extra_info:
        assert data["person_id"] == patron.extra_info["person_id"]
        assert data["department"] == patron.extra_info["department"]
