import ast
import re

from fuji_server.helper.metadata_mapper import Mapper
from fuji_server.helper.metadata_collector import MetaDataCollector


class MetaDataCollectorDublinCore (MetaDataCollector):

    def __init__(self, sourcemetadata, mapping, loggerinst):
        super().__init__(logger=loggerinst, mapping=mapping, sourcemetadata=sourcemetadata)

    def parse_metadata(self):
        dc_core_metadata = {}
        source = None
        if self.source_metadata is not None:
            try:
                self.logger.info('FsF-F2-01M : Extract DublinCore metadata from html page')
                # get core metadat from dublin core meta tags:
                # < meta name = "DCTERMS.element" content = "Value" / >
                # meta_dc_matches = re.findall('<meta\s+([^\>]*)name=\"(DC|DCTERMS)?\.([a-z]+)\"(.*?)content=\"(.*?)\"',self.landing_html)
                exp = '<\s*meta\s*([^\>]*)name\s*=\s*\"(DC|DCTERMS)?\.([A-Za-z]+)(\.[A-Za-z]+)?\"(.*?)content\s*=\s*\"(.*?)\"'
                meta_dc_matches = re.findall(exp, self.source_metadata)
                if len(meta_dc_matches) > 0:
                    self.namespaces.append('http://purl.org/dc/elements/1.1/')
                    source = self.getEnumSourceNames().DUBLINCORE.value
                    dcterms = []

                    for dcitems in self.metadata_mapping.value.values():
                        if isinstance(dcitems, list):
                            dcterms.extend(dcitems)
                        else:
                            dcterms.append(dcitems)
                    for dc_meta in meta_dc_matches:
                        # dc_meta --> ('', 'DC', 'creator', ' ', 'Hillenbrand, Claus-Dieter')
                        k = dc_meta[2]
                        #type
                        t = dc_meta[3]
                        v = dc_meta[5]
                        if k == 'date':
                            if t =='dateAccepted':
                                dc_core_metadata['accepted_date'] = v
                            elif t == 'dateSubmitted':
                                dc_core_metadata['submitted_date'] = v

                        # if self.isDebug:
                        #   self.logger.info('FsF-F2-01M: DublinCore metadata element, %s = %s , ' % (k, v)
                        if k in dcterms:
                            #self.logger.info('FsF-F2-01M: DublinCore metadata element, %s = %s , ' % (k, v))
                            elem = [key for (key, value) in Mapper.DC_MAPPING.value.items() if k in value][0] # fuji ref fields
                            if elem == 'related_resources':
                                #dc_core_metadata['related_resources'] = []
                                # tuple of type and relation
                                if k in ['source']:
                                    t = 'isBasedOn'
                                if k == 'references':
                                    t = 'References'
                                if t in [None, '']:
                                    t = 'isRelatedTo'
                                v = [{'related_resource':v, 'relation_type':t}] # must be a list of dict
                                #v = dict(related_resource=v, relation_type=t)
                            if v:
                                if elem in dc_core_metadata:
                                    if isinstance(dc_core_metadata[elem], list):
                                        if isinstance(v, list):
                                            dc_core_metadata[elem].extend(v)
                                        else:
                                            dc_core_metadata[elem].append(v)
                                    else:
                                        temp_list = []
                                        temp_list.append(dc_core_metadata[elem])
                                        temp_list.append(v)
                                        dc_core_metadata[elem] = temp_list
                                else:
                                    dc_core_metadata[elem] = v
                    if dc_core_metadata.get('related_resources'):
                        count = len([d for d in dc_core_metadata.get('related_resources') if d.get('related_resource')])
                        self.logger.info('FsF-I3-01M : {0} related resource(s) extracted from {1}'.format(count, source))
                    else:
                        self.logger.info('FsF-I3-01M : No related resource(s) found in DublinCore metadata')
            except Exception as e:
                self.logger.exception('Failed to extract DublinCore - {}'.format(e))
        return source, dc_core_metadata
