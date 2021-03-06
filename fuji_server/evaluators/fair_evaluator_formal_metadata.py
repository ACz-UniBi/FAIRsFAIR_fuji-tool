# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2020 PANGAEA (https://www.pangaea.de/)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from fuji_server.evaluators.fair_evaluator import FAIREvaluator
from fuji_server.helper.metadata_collector import MetaDataCollector
from fuji_server.helper.metadata_provider_sparql import SPARQLMetadataProvider
from fuji_server.models.formal_metadata import FormalMetadata
from fuji_server.models.formal_metadata_output import FormalMetadataOutput
from fuji_server.models.formal_metadata_output_inner import FormalMetadataOutputInner

class FAIREvaluatorFormalMetadata(FAIREvaluator):
    def evaluate(self):

        self.result = FormalMetadata(id=self.fuji.count, metric_identifier=self.metric_identifier,
                                            metric_name=self.metric_name)

        outputs = []
        score = 0
        test_status = 'fail'

        # note: 'source' allowed values = ["typed_link", "content_negotiate", "structured_data", "sparql_endpoint"]

        # 1. light-weight check (structured_data), expected keys from extruct ['json-ld','rdfa']
        self.logger.info('{0} : Check of structured data (RDF serialization) embedded in the data page'.format(
            self.metric_identifier))
        if MetaDataCollector.Sources.SCHEMAORG_EMBED.value in self.fuji.metadata_sources:
            outputs.append(FormalMetadataOutputInner(serialization_format='JSON-LD', source='structured_data',
                                                     is_metadata_found=True))
            self.logger.info(
                '{0} : RDF Serialization found in the data page - {1}'.format(self.metric_identifier, 'JSON-LD'))
            score += 1
        elif MetaDataCollector.Sources.RDFA.value in self.fuji.metadata_sources:
            outputs.append(FormalMetadataOutputInner(serialization_format='RDFa', source='structured_data',
                                                     is_metadata_found=True))
            self.logger.info(
                '{0} : RDF Serialization found in the data page - {1}'.format(self.metric_identifier, 'RDFa'))
            score += 1

        if len(outputs) == 0:
            self.logger.info(
                '{0} : NO structured data (RDF serialization) embedded in the data page'.format(self.metric_identifier))

        # 2. hard check (typed-link, content negotiate, sparql endpoint)
        # 2a. in the object page, you may find a <link rel="alternate" type="application/rdf+xml" … />
        # 2b.content negotiate
        formalExists = False
        self.logger.info('{0} : Check if RDF-based typed link included'.format(self.metric_identifier))
        if MetaDataCollector.Sources.RDF_SIGN_POSTING.value in self.fuji.metadata_sources:
            contenttype = self.fuji.rdf_collector.get_content_type()
            self.logger.info(
                '{0} : RDF graph retrieved, content type - {1}'.format(self.metric_identifier, contenttype))
            outputs.append(FormalMetadataOutputInner(serialization_format=contenttype, source='typed_link',
                                                     is_metadata_found=True))
            score += 1
            formalExists = True
        else:
            self.logger.info('{0} : NO RDF-based typed link found'.format(self.metric_identifier))
            self.logger.info(
                '{0} : Check if RDF metadata available through content negotiation'.format(self.metric_identifier))
            if MetaDataCollector.Sources.LINKED_DATA.value in self.fuji.metadata_sources:
                contenttype = self.fuji.rdf_collector.get_content_type()
                self.logger.info(
                    '{0} : RDF graph retrieved, content type - {1}'.format(self.metric_identifier, contenttype))
                outputs.append(FormalMetadataOutputInner(serialization_format=contenttype, source='content_negotiate',
                                                         is_metadata_found=True))
                score += 1
                formalExists = True
            else:
                self.logger.info(
                    '{0} : NO RDF metadata available through content negotiation'.format(self.metric_identifier))

        # 2c. try to retrieve via sparql endpoint (if available)
        if not formalExists:
            # self.logger.info('{0} : Check if SPARQL endpoint is available'.format(formal_meta_identifier))
            # self.sparql_endpoint = 'http://data.archaeologydataservice.ac.uk/sparql/repositories/archives' #test endpoint
            # self.sparql_endpoint = 'http://data.archaeologydataservice.ac.uk/query/' #test web sparql form
            # self.pid_url = 'http://data.archaeologydataservice.ac.uk/10.5284/1000011' #test uri
            # self.sparql_endpoint = 'https://meta.icos-cp.eu/sparqlclient/' #test endpoint
            # self.pid_url = 'https://meta.icos-cp.eu/objects/9ri1elaogsTv9LQFLNTfDNXm' #test uri
            if self.fuji.sparql_endpoint:
                self.logger.info(
                    '{0} : SPARQL endpoint found - {1}'.format(self.metric_identifier, self.fuji.sparql_endpoint))
                sparql_provider = SPARQLMetadataProvider(endpoint=self.fuji.sparql_endpoint, logger=self.logger,
                                                         metric_id=self.metric_identifier)
                query = "CONSTRUCT {{?dataURI ?property ?value}} where {{ VALUES ?dataURI {{ <{}> }} ?dataURI ?property ?value }}".format(
                    self.fuji.pid_url)
                self.logger.info('{0} : Executing SPARQL - {1}'.format(self.metric_identifier, query))
                rdfgraph, contenttype = sparql_provider.getMetadata(query)
                if rdfgraph:
                    outputs.append(
                        FormalMetadataOutputInner(serialization_format=contenttype, source='sparql_endpoint',
                                                  is_metadata_found=True))
                    score += 1
                    self.fuji.namespace_uri.extend(sparql_provider.getNamespaces())
                else:
                    self.logger.warning(
                        '{0} : NO RDF metadata retrieved through the sparql endpoint'.format(self.metric_identifier))
            else:
                self.logger.warning(
                    '{0} : NO SPARQL endpoint found through re3data based on the object URI provided'.format(
                        self.metric_identifier))

        if score > 0:
            test_status = 'pass'
        self.result.test_status = test_status
        self.score.earned = score
        self.result.score = self.score
        self.result.output = outputs