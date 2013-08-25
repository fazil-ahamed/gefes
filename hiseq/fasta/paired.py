# Futures #
from __future__ import division

# Built-in modules #
import os, sys, gzip, tempfile, shutil
from itertools import izip

# Internal modules #
from illumitag.common import property_cached, imean

# Third party modules #
import sh
from Bio import SeqIO

###############################################################################
class PairedFASTQ(object):
    """Read and write FASTQ file pairs without using too much RAM"""
    buffer_size = 1000

    def __len__(self): return self.count
    def __iter__(self): return self.parse()
    def __repr__(self): return '<%s object on "%s">' % (self.__class__.__name__, self.fwd_path)

    def __init__(self, fwd_path, rev_path, parent=None):
        # Basic #
        self.fwd_path = fwd_path
        self.rev_path = rev_path
        # Extra #
        self.pool, self.parent = parent, parent
        self.gziped = True if self.fwd_path.endswith('gz') else False

    @property_cached
    def count(self):
        if self.gziped: return int(sh.zgrep('-c', "^+$", self.fwd_path, _ok_code=[0,1]))
        else: return int(sh.grep('-c', "^+$", self.fwd_path, _ok_code=[0,1]))

    def open(self):
        # Fwd #
        if self.gziped: self.fwd_handle = gzip.open(self.fwd_path, 'r')
        else:           self.fwd_handle = open(self.fwd_path, 'r')
        # Rev #
        if self.gziped: self.rev_handle = gzip.open(self.rev_path, 'r')
        else:           self.rev_handle = open(self.rev_path, 'r')

    def parse(self):
        self.open()
        return izip(SeqIO.parse(self.fwd_handle, 'fastq'),
                    SeqIO.parse(self.rev_handle, 'fastq'))

    def close(self):
        if hasattr(self, 'buffer'): self.flush()
        self.fwd_handle.close()
        self.rev_handle.close()

    def create(self):
        # The buffer #
        self.buffer = []
        self.buf_count = 0
        # Directory #
        self.fwd_dir = os.path.dirname(self.fwd_path)
        self.rev_dir = os.path.dirname(self.rev_path)
        if not os.path.exists(self.fwd_dir): os.makedirs(self.fwd_dir)
        if not os.path.exists(self.rev_dir): os.makedirs(self.rev_dir)
        # The files #
        self.fwd_handle = open(self.fwd_path, 'w')
        self.rev_handle = open(self.rev_path, 'w')

    def add_pair(self, pair):
        self.buffer.append(pair)
        self.buf_count += 1
        if self.buf_count % self.buffer_size == 0:
            sys.stderr.write('.')
            self.flush()

    def flush(self):
        for pair in self.buffer:
            SeqIO.write(pair[0], self.fwd_handle, 'fastq')
            SeqIO.write(pair[1], self.rev_handle, 'fastq')
        self.buffer = []

    def fastqc(self, directory):
        # Symbolic link #
        tmp_dir = tempfile.mkdtemp() + '/'
        if self.gziped: sym_fwd_path = tmp_dir + 'fwd.fastq.gz'
        else:           sym_fwd_path = tmp_dir + 'fwd.fastq'
        if self.gziped: sym_rev_path = tmp_dir + 'rev.fastq.gz'
        else:           sym_rev_path = tmp_dir + 'rev.fastq'
        os.symlink(self.fwd_path, sym_fwd_path)
        os.symlink(self.rev_path, sym_rev_path)
        # Call #
        sh.fastqc(sym_fwd_path, '-q')
        sh.fastqc(sym_rev_path, '-q')
        # Move #
        shutil.move(tmp_dir + 'fwd_fastqc/', directory + "fwd_fastqc/")
        shutil.move(tmp_dir + 'rev_fastqc/', directory + "rev_fastqc/")
        # Clean up #
        shutil.rmtree(tmp_dir)

    @property
    def avg_quality(self):
        self.open()
        fwd_reads = (r for r in SeqIO.parse(self.fwd_handle, "fastq"))
        fwd_scores = (s for r in fwd_reads for s in r.letter_annotations["phred_quality"])
        fwd_mean = imean(fwd_scores)
        rev_reads = (r for r in SeqIO.parse(self.rev_handle, "fastq"))
        rev_scores = (s for r in rev_reads for s in r.letter_annotations["phred_quality"])
        rev_mean = imean(rev_scores)
        self.close()
        return (fwd_mean, rev_mean)

    def cut_in_half(self, new_pair):
        new_pair.create()
        pairs = iter(self)
        for i in xrange(int(len(self)/2)): new_pair.add_pair(pairs.next())
        new_pair.close()
        #shell_output('zcat %s |head -n %i > %s' % (self.fwd_path, len(self)*2, new_pair.fwd_path))
        #shell_output('zcat %s |head -n %i > %s' % (self.rev_path, len(self)*2, new_pair.rev_path))
