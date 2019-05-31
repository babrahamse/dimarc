# variables
fd = u'\u001E' # field delimiter character
sfd = u'\u001F' # subfield delimiter
rd = u'\u001D' # record delimiter

class log:
    def __init__(self):
        self.content = []
        self.output = ''
    def print(self, print_text):
        try:
            self.content.append(print_text)
        except:
            pass # don't bug out
        print(print_text)
    def save(self, filename='log.txt'):
        with open(filename, 'w', encoding='latin_1') as f:
            for line in self.content:
                f.write(line + '\n')

class dimarc:
    ''' dictionary-MARC object
    represents each MARC field as a tuple or dict
    if the field is fixed then we have attr.:val pair: 'field_tag': field data
    if the field is variable then we have a dict:
        'field_tag':
            { 'ind': indicators
              'subfield_count': subfield data }
    '''
    def __init__(self):
        self.data = {}
        self.directory = ''
        self.datablock = ''
        self.leader = ''
        self.rawmarc = ''
        self.meta = ''

class dimarc_collection:
    def __init__(self):
        self.meta = ''
        self.records = []
        self.rawmarc = ''
    def add_from_file(self, filename):
        raw = load_MARC_from_file(filename)
        for rec in raw:
            self.records.append(create_dimarc(rec))
    def serialize_records(self):
        for dimarc_rec in self.records:
            self.rawmarc += convert_dimarc_to_MARC(dimarc_rec)
    def save_MARC(self, filename = 'output.mrc'):
        if self.rawmarc == '':
            raise Exception('You need to serialize back into MARC')
        with open(filename, 'w', encoding='latin_1', newline='') as f:
            f.write(self.rawmarc)
        f.close()

def convert_dimarc_to_MARC(dimarc_obj):
    ''' 
    convert dimarc object back to 'raw' MARC
    :param dimarc_obj: 
    :return: str
    '''
    rcsp = 0 # relative character start pos
    output = ''
    for entry in dimarc_obj.data:
        add_to_datablock = ''
        if entry == 'ldr':
            dimarc_obj.leader = dimarc_obj.data[entry]
            print('record leader is: ' + dimarc_obj.leader)
        elif entry != 'ldr' and len(dimarc_obj.data[entry]) == 2:
            # fixed field
            dimarc_obj.directory += dimarc_obj.data[entry]['tag']
            dimarc_obj.datablock += (fd + dimarc_obj.data[entry]['value'])
            dimarc_obj.directory += prepend_zero(1 + len(dimarc_obj.data[entry]['value']), pad_to=4)
            dimarc_obj.directory += prepend_zero(rcsp, pad_to=5)
            rcsp += 1 + len(dimarc_obj.data[entry]['value'])
        else:
            # variable fields
            dimarc_obj.directory += dimarc_obj.data[entry]['tag']
            add_to_datablock = fd + dimarc_obj.data[entry]['ind']
            for item in dimarc_obj.data[entry]['subfields']:
                add_to_datablock += (sfd + item)
            dimarc_obj.datablock += add_to_datablock
            dimarc_obj.directory += prepend_zero(len(add_to_datablock), pad_to=4)
            dimarc_obj.directory += prepend_zero(rcsp, pad_to=5)
            rcsp += len(add_to_datablock)
    print(dimarc_obj.directory)
    print(dimarc_obj.datablock)
    final = (dimarc_obj.leader + dimarc_obj.directory + dimarc_obj.datablock + fd + rd)
    len_of_rec = prepend_zero(5 + len(final), pad_to=5)
    output = len_of_rec + final
    return output

def prepend_zero(value, pad_to = 4):
    ''' creates right-justified strings, necessary for MARC directory construction
        given value (an integer) and pad_to (integer)
        return value as str, prepended by number of zeroes to pad_to
    '''
    if type(value) is not int:
        raise Exception('Must be int')
    count = 1
    x_val = str(value)
    x_len = len(x_val)
    while count <= (pad_to - x_len):
        x_val = '0' + x_val
        count += 1
    return x_val

def load_MARC_from_file(filename):
    ''' load MARC records from file
        given a filename, returns a list object with rawMARC records
    '''
    output = []
    rawM = ''
    with open(filename, 'r', encoding='latin-1') as f:
        for count, line in enumerate(f):
            rawM += line
    f.close()
    temp = rawM.split(rd)
    for item in list(i for i in temp if i != ''):
        output.append(item)
    print(output)
    return output

def chunk_directory(directory):
    output = []
    dirl = len(directory)

    while dirl > 0:
        current_dir = directory[0:12]
        c_tag = current_dir[0:3]
        output.append(c_tag)
        directory = directory[12:]
        dirl = len(directory)
    return output

def chunk_fields(fields_block):
    output, c_entry_to_add = {}, {}
    data_begins = fields_block.find(fd)

    directory, data = fields_block[0:data_begins], fields_block[data_begins:]
    fields = data.split(fd)

    dir_list = chunk_directory(directory)
    del directory
    del data

    for count, ftag in enumerate(dir_list):
        c_field_tag = ftag
        c_field_data = fields[count + 1]
        field_key = 'field_' + prepend_zero(count, pad_to=3)
        if not sfd in c_field_data:
            c_entry_to_add = {
                field_key: {
                    'tag': c_field_tag,
                    'value': c_field_data}}
        else:
            sf_data = c_field_data.split(sfd)
            indicators = sf_data[0]
            c_entry_to_add = {
                field_key: {
                    'tag': c_field_tag,
                    'ind': sf_data[0],
                    'subfields':[]}}
            for sf in sf_data[1:]:
                c_entry_to_add[field_key]['subfields'].append(sf)

        output.update(c_entry_to_add)
    return output

def create_dimarc(rawmarc):
    ''' create dictionary MARC object
        given raw MARC, and name of object,
        returns dimarc object 
    '''
    output = dimarc()
        
    entry_to_add = {'ldr': rawmarc[5:24]}
    entry_to_add.update((chunk_fields(rawmarc[24:])))
    output.data.update(entry_to_add)

    return output


# test
c = dimarc_collection()
c.meta = 'new collection'
c.add_from_file('test_data_utf8.mrc')
c.serialize_records()
c.save_MARC('test2.mrc')
