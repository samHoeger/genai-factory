# Copyright 2023 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio

import storey

from genai_factory.schemas import WorkflowEvent


class ChainRunner(storey.Flow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_async = asyncio.iscoroutinefunction(self._run)

    def _run(self, event: WorkflowEvent):
        raise NotImplementedError()

    def __call__(self, event: WorkflowEvent):
        return self._run(event)

    def post_init(self,
        mode="sync",
        context=None,
        namespace=None,
        creation_strategy=None,
        **kwargs):
        """
            Finalize post-construction initialization for the runtime or function object.
            :param mode : Execution mode, either "sync" (default) or "async"
            :param context: MLRun context providing metadata, parameters, logging
                for this runtime. Pass `None` if initialization is not tied to a specific run.
            :param namespace: Namespace or project scope in which this object operates (e.g., Kubernetes
                namespace). If not provided, MLRun defaults to the active project namespace.
            :param creation_strategy: Resource creation during initialization (e.g., lazy).
            :param **kwargs: Additional keyword arguments for custom initialization logic (forward compatability in MLRun)
        """
        pass

    async def _do(self, event):
        if event is storey.dtypes._termination_obj:
            return await self._do_downstream(storey.dtypes._termination_obj)
        else:
            print("step name: ", self.name)
            element = self._get_event_or_body(event)
            if self._is_async:
                resp = await self._run(element)
            else:
                resp = self._run(element)
            if resp:
                for key, val in resp.items():
                    element.results[key] = val
                if "answer" in resp:
                    element.query = resp["answer"]
                mapped_event = self._user_fn_output_to_event(event, element)
                await self._do_downstream(mapped_event)


class SessionLoader(storey.Flow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _do(self, event):
        if event is storey.dtypes._termination_obj:
            return await self._do_downstream(storey.dtypes._termination_obj)
        else:
            element = self._get_event_or_body(event)
            if isinstance(element, dict):
                element = WorkflowEvent(**element)

            self.context.session_store.read_state(element)
            mapped_event = self._user_fn_output_to_event(event, element)
            await self._do_downstream(mapped_event)


class HistorySaver(ChainRunner):
    def __init__(
        self,
        answer_key: str = None,
        question_key: str = None,
        save_sources: str = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.answer_key = answer_key
        self.question_key = question_key
        self.save_sources = save_sources

    async def _run(self, event: WorkflowEvent):
        question = (
            event.results[self.question_key]
            if self.question_key
            else event.original_query
        )
        sources = None
        if self.save_sources and "sources" in event.results:
            sources = [src.metadata for src in event.results["sources"]]
            event.results["sources"] = sources
        event.conversation.add_message("Human", question)
        event.conversation.add_message(
            "AI", event.results[self.answer_key or "answer"], sources
        )

        self.context.session_store.save(event)
        return event.results
