import pandas as pd
import numpy as np
import plotly.graph_objects as go

PERSONE_GIURIDICHE_URL = 'https://raw.githubusercontent.com/nicolopomini/techvisory/master/POC_data_PG.csv'
PERSONE_FISICHE_URL = 'https://raw.githubusercontent.com/nicolopomini/techvisory/master/POC_Data_PF.csv'

results_for_people = {}
results_for_pg = {}


def get_dataframe(categoria, drive):
    if categoria == 'PF':
        sep = ";"
        url = PERSONE_FISICHE_URL
    else:
        sep = ","
        url = PERSONE_GIURIDICHE_URL
    if categoria == 'PF':
        Den = 'Nome'
    else:
        Den = 'Denominazione'
    DF = pd.read_csv(url, sep)
    return DF, Den


def get_persona_giuridica():
    return pd.read_csv(PERSONE_GIURIDICHE_URL, ',')

def get_persona_fisica():
    return pd.read_csv(PERSONE_FISICHE_URL, ';')


def analyze_pf_people(df):
    people = df["Nome"].to_list()
    for person in people:
        U1,L1,T,y,Credito = detrazioni('PF',person, 'Nome', df)
        results_for_people[person] = {
            "upper_estimate": U1,
            "lower_estimate": L1,
            "time": T,
            "credito": Credito,
            "credito_for_plot": y
        }

def analyze_pg_people(df):
    people = df["Denominazione"].to_list()
    for person in people:
        U1,L1,T,y,Credito = detrazioni('PG',person, 'Denominazione', df)
        U2, L2, T2 = Liq(person, 'Denominazione', df, 'PG')
        results_for_pg[person] = {
            "upper_estimate": U1,
            "lower_estimate": L1,
            "time": T,
            "credito": Credito,
            "credito_for_plot": y,
            "liquidita_upper": U2,
            "liquidita_lower": L2,
            "liquidita_time": T2
        }


def sell_range(df, person):
    actual_value = check_status(df, person, 'PF', results_for_people[person]["lower_estimate"], 'Nome')
    if actual_value < 0:
        value = actual_value
    else:
        coeff_future_value = future_value(df, person, "PF", results_for_people[person]["time"], results_for_people[person]["lower_estimate"], "Nome", results_for_people[person]["credito"])
        if coeff_future_value < 0:
            value = coeff_future_value
        else:
            A = advantage(df, person, results_for_people[person]["lower_estimate"], 'PF', 'Nome')
            value = A
    if value >= 0:
        return None
    else:
        minimum = results_for_people[person]["credito"] + results_for_people[person]["credito"] * value / 100
        maximum = int(results_for_people[person]["credito"] * 1.05)
        return minimum, maximum


def get_people_that_sell(df):
    people_that_sell = []
    analyze_pf_people(df)
    for person in results_for_people:
        range = sell_range(df, person)
        if range is not None:
            people_that_sell.append(person)
    return people_that_sell

def get_people_to_buy(df, people_that_sell, df_people):
    for business in results_for_pg:
        if sum(results_for_pg[business]["lower_estimate"]) < int(df["Credito"][0]):
            return None
        else:
            people_values = {people: sell_range(df_people, people) for people in people_that_sell}
            sorted_people = {k: v for k, v in sorted(people_values.items(), key=lambda item: item[1][0])}
            budget = int(df["Liquidità 2018"][0])
            total_spent = 0
            bought_people = []
            for people in sorted_people:
                if total_spent + sorted_people[people][0] * 1.02 > budget or total_spent > (sum(results_for_pg[business]["lower_estimate"]) - int(df["Credito"][0])):
                    break
                bought_people.append(people)
                total_spent += sorted_people[people][0]
            return bought_people

def do_offer(people_to_buy, df, df_people):
    analyze_pg_people(df)
    if people_to_buy:
      people_values = {people: sell_range(df_people, people) for people in people_to_buy}
      return {people: (int(people_values[people][0] * 0.98), int(people_values[people][0] * 1.02)) for people in people_values}
    return {}

            



def future_prediction(h, years, Time, variable):
    history = []
    history2 = []
    time = []
    for i in range(len(Time)):
        time.append(Time[i])
    for i in range(len(h)):
        history.append(h[i]), history2.append(h[i])
    for j in range(years):
        c1 = 0
        c2 = 0
        for i in range(len(history) - 1):
            c1 += (history[-1 - i] - history[-2 - i]) * (len(history) - 1 - i)
            c2 += (len(history) - 1 - i)
        c1 = c1 / c2
        if variable == 'Detrazione':
            history.append(max(history[-1] + c1, 0))
        else:
            history.append(history[-1] + c1)
        time.append('20' + str(int(time[-1][2:]) + 1))
        c1 = 0
        c2 = 0
        for i in range(len(history2) - 1):
            c1 += (history2[-1 - i] - history2[-2 - i]) * (1)
            c2 += (1)
        c1 = c1 / c2
        if variable == 'Detrazione':
            history2.append(max(history2[-1] + c1, 0))
        else:
            history2.append(history2[-1] + c1)
    return history, history2, time


def detrazioni(Categoria, Person, Den, DF):
    Var = []
    Var2 = []
    for i in range(len(DF)):
        if DF[Den][i] == Person:
            Credito = (DF['Credito'][i])
            x = []
            Time = []
            value = 0
            for j in DF.keys():
                if Categoria == 'PF':
                    if j[:5] == 'IRPEF':
                        value += DF[j][i]
                        Time.append(j[6:])
                    elif j[:5] == 'Oneri':
                        value -= DF[j][i]
                        x.append(value)
                        value = 0
                else:
                    if j[:25] == "Imposte nette sul reddito":
                        value += DF[j][i]
                        Time.append(j[26:])
                    elif j[:30] == 'Imposte patrimoniali e diverse':
                        value += DF[j][i]
                    elif j[:13] == 'Oneri sociali':
                        value += DF[j][i]
                        x.append(value)
                        value = 0
            Var.append(x)
            Var2.append(x)
    Variable = 'Detrazione'
    Time = np.flip(Time)
    for i in range(len(Var)):
        Var[i] = np.flip(Var[i])
        Var2[i] = np.flip(Var2[i])
    for i in range(len(Var)):
        Var[i], Var2[i], time = future_prediction(Var[i], 5, Time, Variable)
    name = Person
    Upper_estimate = []
    Lower_estimate = []
    y = []
    for i in range(5):
        y.append(Credito * 1.1 * 0.2) 
    for i in range(len(Var[0])):
        Lower_estimate.append(min(Var[0][i], Var2[0][i]))
        Upper_estimate.append(max(Var[0][i], Var2[0][i]))
    return Upper_estimate, Lower_estimate, time, y, Credito


def plot_Detrazioni(T, U1, L1, Person, Categoria, y):
    if Categoria == 'PF':
        index = 5
    else:
        index = 3
    fig = go.Figure(data=[
        go.Scatter(x=T,
                   y=U1,
                   line=dict(width=1, color='rgb(0,150, 0)'),
                   mode='lines+markers',
                   name='Upper estimate'),
        go.Scatter(x=T,
                   y=L1,
                   line=dict(width=1, color='rgb(225,0, 0)'),
                   mode='lines+markers',
                   fillcolor='rgba(68, 68, 68, 0.3)',
                   fill='tonexty',
                   name='Lower estimate')
    ])
    fig.add_trace(
        go.Scatter(x=T[index:],
                   y=y,
                   line=go.scatter.Line(color="black"),
                   name='Credito'))
    fig.update_layout(
        title='Storico e stima della capienza fiscale per ' +
        str(Person),
        xaxis_title="Year",
        yaxis_title="€",
    )
    return fig


def Liq(Person, Den, DF, Categoria):
    Time = []
    for i in range(len(DF)):
        if DF[Den][i] == str(Person):
            if Categoria == 'PG':
                x = []
                for j in DF.keys():
                    if j[:9] == 'Liquidità':
                        x.append(DF[j][i])
                        Time.append(j[10:])
            else:
                x = []
                value = 0
                for j in DF.keys():
                    if j[:10] == 'Imponibile':
                        value += DF[j][i]
                        Time.append(j[11:])
                    elif j[:5] == 'IRPEF':
                        value -= DF[j][i]
                    elif j[:5] == 'Oneri':
                        value += DF[j][i] - 30720
                        x.append(value)
                        value = 0
    x = np.flip(x)
    Time = np.flip(Time)
    Future_Liq, Future_Liq2, Time = future_prediction(x, 5, Time, 'Liquidità')
    Upper_estimate1 = []
    Lower_estimate1 = []
    for i in range(len(Future_Liq)):
        Lower_estimate1.append(min(Future_Liq[i], Future_Liq2[i]))
        Upper_estimate1.append(max(Future_Liq[i], Future_Liq2[i]))
    return Upper_estimate1, Lower_estimate1, Time


def plot_Liq(U, L, T, Person):
    fig = go.Figure(data=[
        go.Scatter(x=T,
                   y=U,
                   line=dict(width=1, color='rgb(0,150, 0)'),
                   mode='lines+markers',
                   name='Upper estimate'),
        go.Scatter(x=T,
                   y=L,
                   line=dict(width=1, color='rgb(225,0, 0)'),
                   mode='lines+markers',
                   fillcolor='rgba(68, 68, 68, 0.3)',
                   fill='tonexty',
                   name='Lower estimate')
    ])
    fig.update_layout(
        title='Storico e stima della capacità finanziaria per ' + str(Person),
        xaxis_title="Year",
        yaxis_title="€",
    )
    return fig


def plot_gauge(coeff):
    fig = go.Figure(
        go.Indicator(domain={
            'x': [0, 1],
            'y': [0, 1]
        },
                     value=coeff,
                     mode="gauge+number",
                     title={'text': "Advantage"},
                     delta={'reference': 0},
                     gauge={
                         'axis': {
                             'range': [-5, 5]
                         },
                         'bar': {
                             'color': "black"
                         },
                         'steps': [
                             {
                                 'range': [-5, -1],
                                 'color': "red"
                             },
                             {
                                 'range': [-1, 0],
                                 'color': "yellow"
                             },
                             {
                                 'range': [0, 5],
                                 'color': "green"
                             },
                         ],
                     }))
    fig.show()


def check_status(DF, Person, Categoria, Lower_estimate, Den):
    c1 = 0
    c2 = 0
    for i in range(len(DF)):
        if DF[Den][i] == str(Person):
            Credito = DF['Credito'][i]
            counter = 0
            for j in DF.keys():
                if Categoria == 'PG':
                    if str(j[:3]) == 'Liq':
                        if DF[j][i] < 0:
                            c1 -= 5 * (5 - counter)
                        c2 += (5 - counter)
                        counter += 1
                else:
                    value = 0
                    if j[:10] == 'Imponibile':
                        value += DF[j][i]
                    elif j[:5] == 'IRPEF':
                        value -= DF[j][i]
                    elif j[:5] == 'Oneri':
                        value += DF[j][i]
                        if DF[j][i] < 0:
                            c1 -= 5 * (5 - counter)
                        c2 += (5 - counter)
                        counter += 1
                        value = 0
            c1 = c1 / c2
            c3 = 0
            for j in DF.keys():
                if str(j) == 'Sofferenza':
                    if DF[j][i] < 0:
                        c3 = -5
    coeff = min(c1, c3)
    if Categoria == 'PF':
        index = 5
    else:
        index = 3
    somma = 0
    for i in range(5):
        if Lower_estimate[index + i] >= (Credito * 1.1 * 0.2):
            somma += Credito * 1.1 * 0.2
        else:
            somma += Lower_estimate[5 + i]
    if coeff < 0:
        return coeff
    else:
        return coeff


def future_value(DF, Person, Categoria, Time, Lower_estimate, Den, Credito):
    for i in range(len(DF)):
        if DF[Den][i] == str(Person):
            if Categoria == 'PG':
                x = []
                for j in DF.keys():
                    if j[:9] == 'Liquidità':
                        x.append(DF[j][i])
                        Time.append(j[10:])
            else:
                x = []
                value = 0
                for j in DF.keys():
                    if j[:10] == 'Imponibile':
                        value += DF[j][i]
                        Time.append(j[11:])
                    elif j[:5] == 'IRPEF':
                        value -= DF[j][i]
                    elif j[:5] == 'Oneri':
                        value += DF[j][i]
                        x.append(value)
                        value = 0
    x = np.flip(x)
    Future_Liq, Future_Liq2, Time = future_prediction(x, 5, Time, 'Liquidità')

    Upper_estimate1 = []
    Lower_estimate1 = []
    for i in range(len(Future_Liq)):
        Lower_estimate1.append(min(Future_Liq[i], Future_Liq2[i]))
        Upper_estimate1.append(max(Future_Liq[i], Future_Liq2[i]))
    future_value = 0
    c2 = 0
    for i in range(len(Lower_estimate1) - 5):
        if Lower_estimate1[5 + i] < 0:
            future_value -= 1 * (1 / (1 + i))
        c2 += (1 / (1 + i))
    if Categoria == 'PF':
        index = 5
    else:
        index = 3
    somma = 0
    for i in range(5):
        if Lower_estimate[index + i] >= (Credito * 1.1 * 0.2):
            somma += Credito * 1.1 * 0.2
        else:
            somma += Lower_estimate1[5 + i]

    if c2 > 0:
        future_value /= c2
        #print ("Consigliato vendere il credito nel range: ["+str(int(minimum))+"€,"+str(Credito*1.05)+"€]")
        return future_value
    else:
        return future_value


def advantage(DF, Person, Lower_estimate, Categoria, Den):
    if Categoria == 'PF':
        index = 5
    else:
        index = 3
    for i in range(len(DF)):
        if DF[Den][i] == str(Person):
            Credito = DF['Credito'][i]
    somma = 0
    for i in range(5):
        if Lower_estimate[index + i] >= (Credito * 1.1 * 0.2):
            somma += Credito * 1.1 * 0.2
        else:
            somma += Lower_estimate[5 + i]
    if somma >= Credito * 1.05:
        #print ("Consigliato non vendere")
        return (somma - Credito * 1.05) / ((Credito * 1.05 - Credito) / 5)
    else:
        value = -(somma) / (Credito * 1.05)
        #print ("Consigliato vendere nel range: ["+str(int(somma))+","+str(Credito*1.05)+"€]")
        return value


def final_coeff(DF, Person, Categoria, Lower_estimate, Time, Credito, Den):
    actual_value = check_status(DF, Person, Categoria, Lower_estimate, Den)
    if actual_value < 0:
        value = actual_value
    else:
        coeff_future_value = future_value(DF, Person, Categoria, Time,
                                          Lower_estimate, Den, Credito)
        if coeff_future_value < 0:
            value = coeff_future_value
        else:
            A = advantage(DF, Person, Lower_estimate, Categoria, Den)
            value = A
    if value >= 0:
        print("Consigliato non vendere")
    else:
        minimum = Credito + Credito * value / 100
        print("Consigliato vendere il credito nel range: [" +
              str(int(minimum)) + "€," + str(int(Credito * 1.05)) + "€]")
    return value
