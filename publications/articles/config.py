# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# CESNET OA Publication Repository is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from functools import partial

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Bool
from flask_security.utils import _
from invenio_records_rest.facets import terms_filter, range_filter
from invenio_records_rest.utils import allow_all, deny_all, check_elasticsearch
from oarepo_communities.links import community_record_links_factory
from oarepo_communities.search import community_search_factory
from oarepo_multilingual import language_aware_text_match_filter
from oarepo_records_draft import DRAFT_IMPORTANT_FACETS, DRAFT_IMPORTANT_FILTERS
from oarepo_ui import translate_facets, translate_filters, translate_facet

from publications.articles.constants import ARTICLE_PID_TYPE, ARTICLE_DRAFT_PID_TYPE, ARTICLE_ALL_PID_TYPE, \
    ARTICLE_DRAFT_RECORD_CLASS, ARTICLE_RECORD_CLASS, ARTICLE_ALL_RECORD_CLASS
from publications.articles.record import published_index_name, draft_index_name, all_index_name
from publications.articles.search import ArticleRecordsSearch
from publications.indexer import CommitingRecordIndexer
from publications.links import publications_links_factory

RECORDS_DRAFT_ENDPOINTS = {
    'articles': {
        'draft': 'draft-articles',

        'pid_type': ARTICLE_PID_TYPE,
        'pid_minter': 'publications-article',
        'pid_fetcher': 'publications-article',
        'default_endpoint_prefix': True,

        'record_class': ARTICLE_RECORD_CLASS,
        'links_factory_imp': partial(community_record_links_factory, original_links_factory=publications_links_factory),

        # Who can publish a draft article record
        'publish_permission_factory_imp': 'publications.articles.permissions.publish_draft_object_permission_impl',
        # Who can unpublish (delete published & create a new draft version of)
        # a published article record
        'unpublish_permission_factory_imp': 'publications.articles.permissions.unpublish_draft_object_permission_impl',
        # Who can edit (create a new draft version of) a published dataset record
        'edit_permission_factory_imp': 'publications.articles.permissions.update_object_permission_impl',
        # Who can enumerate published articles
        'list_permission_factory_imp': allow_all,
        # Who can view a detail of an existing published article
        'read_permission_factory_imp': allow_all,
        # Make sure everything else is for biden
        'create_permission_factory_imp': deny_all,
        'update_permission_factory_imp': deny_all,
        'delete_permission_factory_imp': deny_all,

        'default_media_type': 'application/json',
        'indexer_class': CommitingRecordIndexer,
        'search_class': ArticleRecordsSearch,
        'search_factory_imp': community_search_factory,
        'search_index': published_index_name,
        'search_serializers': {
            'application/json': 'oarepo_validate:json_search',
        },

        'list_route': '/<community_id>/articles/published/',  # will not be used
        'item_route':
            f'/<commpid({ARTICLE_PID_TYPE},model="articles",record_class="{ARTICLE_RECORD_CLASS}"):pid_value>',
        'files': dict(
            # File attachments are currently not allowed on article records
            put_file_factory=deny_all,
            get_file_factory=deny_all,
            delete_file_factory=deny_all
        )
    },
    'draft-articles': {
        'pid_type': ARTICLE_DRAFT_PID_TYPE,
        'search_class': ArticleRecordsSearch,
        'search_index': draft_index_name,
        'search_factory_imp': community_search_factory,
        'search_serializers': {
            'application/json': 'oarepo_validate:json_search',
        },
        'record_serializers': {
            'application/json': 'oarepo_validate:json_response',
        },
        'record_class': ARTICLE_DRAFT_RECORD_CLASS,
        'links_factory_imp': partial(community_record_links_factory, original_links_factory=publications_links_factory),

        # Who can create a new draft article record?
        'create_permission_factory_imp': 'publications.articles.permissions.create_draft_object_permission_impl',
        # Who can edit an existing draft article record
        'update_permission_factory_imp': 'publications.articles.permissions.update_draft_object_permission_impl',
        # Who can view an existing draft article record
        'read_permission_factory_imp': 'publications.articles.permissions.read_draft_object_permission_impl',
        # Who can delete an existing draft article record
        'delete_permission_factory_imp': 'publications.articles.permissions.delete_draft_object_permission_impl',
        # Who can enumerate a draft article record collection
        'list_permission_factory_imp': 'publications.articles.permissions.list_draft_object_permission_impl',

        'list_route': '/<community_id>/articles/draft/',
        'item_route':
            f'/<commpid({ARTICLE_DRAFT_PID_TYPE},model="articles/draft",record_class="{ARTICLE_DRAFT_RECORD_CLASS}"):pid_value>',
        'record_loaders': {
            'application/json-patch+json': 'oarepo_validate.json_loader',
            'application/json': 'oarepo_validate.json_files_loader'
        },
        'files': dict(
            # File attachments are currently not allowed on article records
            put_file_factory=deny_all,
            get_file_factory=deny_all,
            delete_file_factory=deny_all
        )
    }
}

RECORDS_REST_ENDPOINTS = {
    # readonly url for both endpoints, does not have item route
    # as it is accessed from the endpoints above
    'all-community-articles': dict(
        pid_type=ARTICLE_ALL_PID_TYPE + '-community-all',
        pid_minter='all-publications-articles',
        pid_fetcher='all-publications-articles',
        default_endpoint_prefix=True,
        record_class=ARTICLE_ALL_RECORD_CLASS,
        search_class=ArticleRecordsSearch,
        search_index=all_index_name,
        search_factory_imp=community_search_factory,
        search_serializers={
            'application/json': 'oarepo_validate:json_search',
        },
        list_route='/<community_id>/articles/all/',
        default_media_type='application/json',
        max_result_window=10000,
        links_factory_imp=partial(community_record_links_factory, original_links_factory=publications_links_factory),

        # not used really
        item_route=f'/articles'
                   f'/not-used-but-must-be-present',
        list_permission_factory_imp=allow_all,
        create_permission_factory_imp=deny_all,
        delete_permission_factory_imp=deny_all,
        update_permission_factory_imp=deny_all,
        read_permission_factory_imp=check_elasticsearch,
        record_serializers={
            'application/json': 'oarepo_validate:json_response',
        },
        use_options_view=False,
    ),
    'all-articles': dict(
        pid_type=ARTICLE_ALL_PID_TYPE,
        pid_minter='all-publications-articles',
        pid_fetcher='all-publications-articles',
        default_endpoint_prefix=True,
        record_class=ARTICLE_ALL_RECORD_CLASS,
        search_class=ArticleRecordsSearch,
        search_index=all_index_name,
        search_factory_imp=community_search_factory,
        search_serializers={
            'application/json': 'oarepo_validate:json_search',
        },
        list_route='/articles/all/',
        default_media_type='application/json',
        max_result_window=10000,
        links_factory_imp=partial(community_record_links_factory, original_links_factory=publications_links_factory),

        # not used really
        item_route=f'/articles'
                   f'/not-used-but-must-be-present',
        list_permission_factory_imp=allow_all,
        create_permission_factory_imp=deny_all,
        delete_permission_factory_imp=deny_all,
        update_permission_factory_imp=deny_all,
        read_permission_factory_imp=check_elasticsearch,
        record_serializers={
            'application/json': 'oarepo_validate:json_response',
        },
        use_options_view=False,
    )
}


def boolean_filter(field):
    def val2bool(x):
        if x == '1' or x == 'true' or x is True:
            return True
        return False

    def inner(values):
        return Q('terms', **{field: [val2bool(x) for x in values]})

    return inner


def date_year_range(field, start_date_math=None, end_date_math=None, **kwargs):
    def inner(values):
        range_values = [f'{v}-01--{v}-12' for v in values]
        return range_filter(field, start_date_math, end_date_math, **kwargs)(range_values)

    return inner


def state_terms_filter(field):
    def inner(values):
        if 'filling' in values:
            return Bool(should=[
                Q('terms', **{field: values}),
                Bool(
                    must_not=[
                        Q('exists', field='state')
                    ]
                )
            ], minimum_should_match=1)
        else:
            return Q('terms', **{field: values})

    return inner


FILTERS = {
    _('category'): terms_filter('category'),
    _('creator'): terms_filter('creator.raw'),
    _('title'): language_aware_text_match_filter('title'),
    _('state'): state_terms_filter('state'),
    # draft
    **DRAFT_IMPORTANT_FILTERS
}


def term_facet(field, order='desc', size=100, missing=None):
    ret = {
        'terms': {
            'field': field,
            'size': size,
            "order": {"_count": order}
        },
    }
    if missing is not None:
        ret['terms']['missing'] = missing
    return ret


FACETS = {
    'state': translate_facet(term_facet('state', missing='filling'), possible_values=[
        _('filling'),
        _('approving'),
        _('approved'),
        _('published'),
        _('deleted')
    ]),
    'creator': term_facet('creator.raw'),
    **DRAFT_IMPORTANT_FACETS
}

RECORDS_REST_FACETS = {
    'draft-articles-publication-article-v1.0.0': {
        'aggs': translate_facets(FACETS, label='{facet_key}', value='{value_key}'),
        'filters': translate_filters(FILTERS, label='{filter_key}')
    },
    'articles-publication-article-v1.0.0': {
        'aggs': translate_facets(FACETS, label='{facet_key}'),
        'filters': translate_filters(FILTERS, label='{filter_key}')
    },
    'all-articles': {
        'aggs': translate_facets(FACETS, label='{facet_key}'),
        'filters': translate_filters(FILTERS, label='{filter_key}')
    },
}

RECORDS_REST_SORT_OPTIONS = {
    'all-articles': {
        'alphabetical': {
            'title': 'alphabetical',
            'fields': [
                'title.cs.raw'
            ],
            'default_order': 'asc',
            'order': 1
        },
        'best_match': {
            'title': 'Best match',
            'fields': ['_score'],
            'default_order': 'desc',
            'order': 1,
        }
    }
}

RECORDS_REST_DEFAULT_SORT = {
    'all-articles': {
        'query': 'best_match',
        'noquery': 'alphabetical'
    }
}
