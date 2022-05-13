from rdflib import BNode, Literal, URIRef

EXTRA_RESOURCE_TRIPLES = [
    (URIRef('http://publications.europa.eu/resource/authority/language/POL'),
     URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
     URIRef('http://purl.org/dc/terms/LinguisticSystem')),

    (URIRef('http://publications.europa.eu/resource/authority/language/POL'),
     URIRef('http://www.w3.org/2004/02/skos/core#inScheme'),
     URIRef('http://publications.europa.eu/resource/authority/language')),

    (URIRef('http://publications.europa.eu/resource/authority/language/ENG'),
     URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
     URIRef('http://purl.org/dc/terms/LinguisticSystem')),

    (URIRef('http://publications.europa.eu/resource/authority/language/ENG'),
     URIRef('http://www.w3.org/2004/02/skos/core#inScheme'),
     URIRef('http://publications.europa.eu/resource/authority/language')),

    (URIRef('http://purl.org/adms/status/Completed'),
     URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
     URIRef('http://www.w3.org/2004/02/skos/core#Concept')),

    (URIRef('http://purl.org/adms/status/Completed'),
     URIRef('http://www.w3.org/2004/02/skos/core#prefLabel'),
     Literal('Completed', lang='en')),

    (URIRef('http://purl.org/adms/status/Completed'),
     URIRef('http://www.w3.org/2004/02/skos/core#inScheme'),
     URIRef('http://purl.org/adms/status/1.0')),

    (URIRef('http://purl.org/adms/status/1.0'),
     URIRef('http://purl.org/dc/terms/title'),
     Literal('Status', lang='en')),

    (URIRef('http://purl.org/adms/status/1.0'),
     URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
     URIRef('http://www.w3.org/2004/02/skos/core#ConceptScheme')),
]

EXTRA_DATASET_TRIPLES = EXTRA_RESOURCE_TRIPLES + [
    (URIRef('http://publications.europa.eu/resource/authority/file-type/XML'),
     URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
     URIRef('http://purl.org/dc/terms/MediaTypeOrExtent')),

    (URIRef('http://publications.europa.eu/resource/authority/file-type/XML'),
     URIRef('http://www.w3.org/2004/02/skos/core#inScheme'),
     URIRef('http://publications.europa.eu/resource/authority/file-type')),

    (BNode('VcardKind'),
     URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
     URIRef('http://www.w3.org/2006/vcard/ns#Kind')),

    (BNode('VcardKind'),
     URIRef('http://www.w3.org/2006/vcard/ns#fn'),
     Literal('KPRM', datatype=URIRef('http://www.w3.org/2001/XMLSchema#string'))),

    (BNode('VcardKind'),
     URIRef('http://www.w3.org/2006/vcard/ns#hasEmail'),
     URIRef('mailto:kontakt@dane.gov.pl')),

    (URIRef('http://publications.europa.eu/resource/authority/frequency/DAILY'),
     URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
     URIRef('http://purl.org/dc/terms/Frequency')),

    (URIRef('http://publications.europa.eu/resource/authority/frequency/DAILY'),
     URIRef('http://www.w3.org/2004/02/skos/core#inScheme'),
     URIRef('http://publications.europa.eu/resource/authority/frequency')),

    (URIRef('http://publications.europa.eu/resource/authority/language/ENG'),
     URIRef('http://www.w3.org/2004/02/skos/core#inScheme'),
     URIRef('http://publications.europa.eu/resource/authority/language')),
]
