# **CORAE** - **Co**ntinuous **R**etrospective **A**ffect **E**valuation

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Description

This is the repository that contains source code for CORAE.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Install from source:

#### 1. Clone the CORAE repository to your local machine

```bash
$ git clone https://www.github.com/mjsack/CORAE.git
```

#### 2. Run <code>build.sh</code> to install any outstanding dependencies

```bash
$ bash build.sh
```

## Usage

### Preparing to deploy:

#### 1. Modify <code>config.ini</code> according to the needs of your project

```bash
$ cd documents
$ nano config.ini
```

### Deploying your instance:

#### 1. Run <code>deploy.sh</code> to generate user dashboards and initialize your secure tunnel

#### 2. Distribute the uniquely generated dashboard URLs to your participants

##### - By default these are generated in the <code>/live/</code> directory

## Configuration

<p>We developed <code>CORAE</code> with the goal of creating an accessible tool for researchers to gather continuous affect data. To this end, we have attempted to make the process of project configuration as intuitive as possible.</p>

<p>Prior to running <code>deploy.sh</code> you may change parameters within <code>config.ini</code> to alter frontend and backend components of the annotation dashboard.</p>

## License

Copyright (c) 2021-2023 Cornell University

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
