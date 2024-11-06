import React from 'react';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import { ApolloClient } from 'apollo-client';
import { InMemoryCache } from 'apollo-cache-inmemory';
import { ApolloProvider /* , graphql */ } from 'react-apollo';

import AppRoot from './AppRoot';
import { GQL_HOST } from './config';
import { themePalette } from './data/ui_constants';

// Custom fetch handler from Jay Densic - https://github.com/jaydenseric/apollo-upload-client/issues/88
// Creates a custom fetch wrapper that reports upload status percentage.
const parseHeaders = (rawHeaders) => {
  const headers = new Headers();
  // Replace instances of \r\n and \n followed by at least one space or horizontal tab with a space
  // https://tools.ietf.org/html/rfc7230#section-3.2
  const preProcessedHeaders = rawHeaders.replace(/\r?\n[\t ]+/g, " ");
  preProcessedHeaders.split(/\r?\n/).forEach((line) => {
    const parts = line.split(":");
    const key = parts.shift().trim();
    if (key) {
      const value = parts.join(":").trim();
      headers.append(key, value);
    }
  });
  return headers;
};

export const uploadFetch = (url, options) =>
    new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.onload = () => {
        const opts = {
          status: xhr.status,
          statusText: xhr.statusText,
          headers: parseHeaders(xhr.getAllResponseHeaders() || "")
        };
        opts.url =
            "responseURL" in xhr
                ? xhr.responseURL
                : opts.headers.get("X-Request-URL");
        const body = "response" in xhr ? xhr.response : (xhr).responseText;
        resolve(new Response(body, opts));
      };
      xhr.onerror = () => {
        reject(new TypeError("Network request failed"));
      };
      xhr.ontimeout = () => {
        reject(new TypeError("Network request failed"));
      };
      xhr.open(options.method, url, true);

      Object.keys(options.headers).forEach(key => {
        xhr.setRequestHeader(key, options.headers[key]);
      });

      if (xhr.upload) {
        xhr.upload.onprogress = options.onProgress;
      }

      xhr.send(options.body);
    });

const customFetch = (uri, options) => {
  if (options.useUpload) {
    return uploadFetch(uri, options);
  }
  return fetch(uri, options);
};


// NOTE: If you want to get direct access to your ApolloClient instance that is provided by <ApolloProvider/> in your
// components, then be sure to look at the withApollo() enhancer function, which will create a new component which
// passes in an instance of ApolloClient as a 'client' prop.
// If you are wondering when to use withApollo() and when to use graphql(), the answer is that most of the time you will
// want to use graphql().
// Ref: withApollo - https://www.apollographql.com/docs/react/api/react-apollo.html#withApollo
// Ref: graphql() -  https://www.apollographql.com/docs/react/api/react-apollo.html#graphql
// Ref: Example using withApollo: https://www.apollographql.com/docs/react/advanced/caching.html#reset-store
const { HttpLink } = require('apollo-link-http');
const client = new ApolloClient({
    uri: GQL_HOST,
    link: new HttpLink({
        uri: GQL_HOST,
    }),
    cache: new InMemoryCache()
});


// Alternate client for uploads so they don't block other queries
const { createUploadLink } = require('apollo-upload-client');
const uploadClient = new ApolloClient({
    link: createUploadLink({
        uri: GQL_HOST,
        credentials: 'same-origin',
        fetch: typeof window === 'undefined' ? global.fetch : customFetch,
    }),
    cache: new InMemoryCache()
});


// Create our custom theme based on our palette colors
const customTheme = createMuiTheme(themePalette);

// Stateless Component - Simply returns JSX elements. So no need for curly braces (either use parenthesis or none OK).
const App = () => (
  <MuiThemeProvider theme={customTheme}>
    <ApolloProvider client={client}>
      <AppRoot client={client} uploadClient={uploadClient}/>
    </ApolloProvider>
  </MuiThemeProvider>
);

export default App;
