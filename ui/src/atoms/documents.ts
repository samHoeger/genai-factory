// Copyright 2024 Iguazio
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import Client from '@services/Api';
import { Document } from '@shared/types/document';
import { atom } from 'jotai';

export const documentsAtom = atom<Document[]>([]);

export const documentsLoadingAtom = atom<boolean>(false);

export const documentsErrorAtom = atom<string | null>(null);


export const documentsWithFetchAtom = atom(
  (get) => get(documentsAtom),
  async (_get, set, projectName) => {
    set(documentsLoadingAtom, true);
    set(documentsErrorAtom, null);
    try {
      const documents = await Client.getDocuments(projectName as string);
      const sortedDocuments = documents.data.sort((a: Document, b: Document) => {
        const dateA = new Date(a.created as string);
        const dateB = new Date(b.created as string);
        return dateA.getTime() - dateB.getTime();
      });
      set(documentsAtom, sortedDocuments);
    } catch (error) {
      set(documentsErrorAtom, 'Failed to fetch documents');
    } finally {
      set(documentsLoadingAtom, false);
    }
  }
);

export const selectedDocumentAtom = atom<Document>({ name: '', description: '', labels: {}, owner_id: '', project_id: '', path: '' });
