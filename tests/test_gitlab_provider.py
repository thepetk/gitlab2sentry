from datetime import datetime

import aiohttp
from gitlab import Gitlab
from gql.transport.aiohttp import AIOHTTPTransport

from gitlab2sentry.resources import (
    GITLAB_PROJECT_CREATION_LIMIT,
    GRAPHQL_FETCH_PROJECT_QUERY,
    GRAPHQL_LIST_PROJECTS_QUERY,
    GRAPHQL_TEST_QUERY,
    TEST_GITLAB_TOKEN,
    TEST_GITLAB_URL,
)
from tests.conftest import CURRENT_TIME


def test_get_transport(gql_client_fixture):
    assert isinstance(
        gql_client_fixture._get_transport(TEST_GITLAB_URL, TEST_GITLAB_TOKEN),
        AIOHTTPTransport,
    )


def test_query(gql_client_fixture, payload_new_project, mocker):
    mocker.patch.object(
        gql_client_fixture._client,
        attribute="execute",
        return_value=[payload_new_project],
    )
    assert gql_client_fixture._query(
        payload_new_project["node"]["name"], GRAPHQL_TEST_QUERY["body"]
    )
    mocker.patch.object(
        gql_client_fixture._client,
        attribute="execute",
        side_effect=aiohttp.client_exceptions.ClientResponseError(None, None),
    )
    assert not gql_client_fixture._query(
        payload_new_project["node"]["name"], GRAPHQL_TEST_QUERY["body"]
    )


def test_project_fetch_query(gql_client_fixture, payload_new_project, mocker):
    mocker.patch.object(
        gql_client_fixture._client,
        attribute="execute",
        return_value=[payload_new_project],
    )
    assert (
        gql_client_fixture.project_fetch_query(GRAPHQL_FETCH_PROJECT_QUERY)[0]
        == payload_new_project
    )


def test_project_list_query(gql_client_fixture, payload_new_project, mocker):
    mocker.patch.object(
        gql_client_fixture._client,
        attribute="execute",
        return_value=[payload_new_project],
    )
    assert (
        gql_client_fixture.project_list_query(GRAPHQL_LIST_PROJECTS_QUERY, None)[0]
        == payload_new_project
    )


def test_get_gitlab(gitlab_provider_fixture):
    assert isinstance(
        gitlab_provider_fixture._get_gitlab(TEST_GITLAB_URL, TEST_GITLAB_TOKEN), Gitlab
    )


def test_get_update_limit(gitlab_provider_fixture):
    if GITLAB_PROJECT_CREATION_LIMIT:
        assert (
            datetime.now() - gitlab_provider_fixture._get_update_limit()
        ).days - GITLAB_PROJECT_CREATION_LIMIT <= 1
    else:
        assert not gitlab_provider_fixture._get_update_limit()


def test_from_iso_to_datetime(gitlab_provider_fixture):
    assert isinstance(
        gitlab_provider_fixture._from_iso_to_datetime(CURRENT_TIME), datetime
    )


def test_get_project(gitlab_provider_fixture, mocker):
    mocker.patch.object(
        gitlab_provider_fixture._gql_client,
        attribute="project_fetch_query",
        return_value=True,
    )
    assert gitlab_provider_fixture.get_project(GRAPHQL_FETCH_PROJECT_QUERY) is True


def test_get_all_projects(
    gitlab_provider_fixture, payload_new_project, payload_old_project, mocker
):
    mocker.patch.object(
        gitlab_provider_fixture._gql_client,
        attribute="project_list_query",
        side_effect=[
            {
                GRAPHQL_LIST_PROJECTS_QUERY["instance"]: {
                    "edges": [payload_new_project],
                    "pageInfo": {"endCursor": "first-cursor", "hasNextPage": True},
                }
            },
            {
                GRAPHQL_LIST_PROJECTS_QUERY["instance"]: {
                    "edges": [payload_new_project],
                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                }
            },
        ],
    )
    assert (
        len(
            [
                result_page
                for result_page in gitlab_provider_fixture.get_all_projects(
                    GRAPHQL_LIST_PROJECTS_QUERY
                )
            ]
        )
        == 2
    )

    mocker.patch.object(
        gitlab_provider_fixture._gql_client,
        attribute="project_list_query",
        side_effect=[
            {
                GRAPHQL_LIST_PROJECTS_QUERY["instance"]: {
                    "edges": [payload_old_project],
                    "pageInfo": {"endCursor": "first-cursor", "hasNextPage": True},
                }
            },
            {
                GRAPHQL_LIST_PROJECTS_QUERY["instance"]: {
                    "edges": [payload_old_project],
                    "pageInfo": {"endCursor": None, "hasNextPage": False},
                }
            },
        ],
    )
    assert (
        len(
            [
                result_page
                for result_page in gitlab_provider_fixture.get_all_projects(
                    GRAPHQL_LIST_PROJECTS_QUERY
                )
            ]
        )
        == 1
    )